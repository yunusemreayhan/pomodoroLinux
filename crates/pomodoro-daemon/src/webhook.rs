use crate::db::{self, Pool};

static WEBHOOK_CLIENT: std::sync::OnceLock<reqwest::Client> = std::sync::OnceLock::new();
fn webhook_client() -> &'static reqwest::Client {
    WEBHOOK_CLIENT.get_or_init(|| reqwest::Client::builder().timeout(std::time::Duration::from_secs(10)).build().unwrap_or_default())
}

/// Fire webhooks for an event in the background. Non-blocking, errors are logged.
pub fn dispatch(pool: Pool, event: &str, payload: serde_json::Value) {
    let event = event.to_string();
    tokio::spawn(async move {
        let hooks = match db::get_active_webhooks(&pool, &event).await {
            Ok(h) => h,
            Err(e) => { tracing::warn!("Failed to load webhooks: {}", e); return; }
        };
        let client = webhook_client();
        for hook in hooks {
            let body = serde_json::json!({ "event": &event, "data": &payload });
            let body_str = serde_json::to_string(&body).unwrap_or_default();
            let mut req = client.post(&hook.url)
                .header("content-type", "application/json")
                .header("x-pomodoro-event", &event)
                .body(body_str.clone());
            if let Some(ref secret) = hook.secret {
                use sha2::{Sha256, Digest};
                // HMAC-like: SHA256(secret + body)
                let mut hasher = Sha256::new();
                hasher.update(secret.as_bytes());
                hasher.update(body_str.as_bytes());
                let sig = hasher.finalize().iter().map(|b| format!("{:02x}", b)).collect::<String>();
                req = req.header("x-pomodoro-signature", format!("sha256={}", sig));
            }
            let mut attempts = 0;
            loop {
                attempts += 1;
                match req.try_clone().unwrap_or_else(|| client.post(&hook.url).body(body_str.clone())).send().await {
                    Ok(resp) if resp.status().is_success() => break,
                    Ok(resp) => {
                        tracing::warn!("Webhook {} returned {}", hook.url, resp.status());
                        if attempts >= 3 { break; }
                    }
                    Err(e) => {
                        tracing::warn!("Webhook {} attempt {}/3 failed: {}", hook.url, attempts, e);
                        if attempts >= 3 { break; }
                    }
                }
                tokio::time::sleep(std::time::Duration::from_secs(1 << attempts)).await;
            }
        }
    });
}

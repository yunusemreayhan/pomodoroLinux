use crate::db::{self, Pool};

/// Fire webhooks for an event in the background. Non-blocking, errors are logged.
pub fn dispatch(pool: Pool, event: &str, payload: serde_json::Value) {
    let event = event.to_string();
    tokio::spawn(async move {
        let hooks = match db::get_active_webhooks(&pool, &event).await {
            Ok(h) => h,
            Err(e) => { tracing::warn!("Failed to load webhooks: {}", e); return; }
        };
        let client = reqwest::Client::builder().timeout(std::time::Duration::from_secs(10)).build().unwrap_or_default();
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
            if let Err(e) = req.send().await {
                tracing::warn!("Webhook {} failed: {}", hook.url, e);
            }
        }
    });
}

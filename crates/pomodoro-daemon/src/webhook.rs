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
                // HMAC signature: hex(hash(secret + body))
                use std::collections::hash_map::DefaultHasher;
                use std::hash::{Hash, Hasher};
                let mut h = DefaultHasher::new();
                secret.hash(&mut h);
                body_str.hash(&mut h);
                req = req.header("x-pomodoro-signature", format!("{:016x}", h.finish()));
            }
            if let Err(e) = req.send().await {
                tracing::warn!("Webhook {} failed: {}", hook.url, e);
            }
        }
    });
}

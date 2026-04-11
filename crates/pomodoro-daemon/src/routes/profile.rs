use super::*;


#[utoipa::path(put, path = "/api/profile", request_body = UpdateProfileRequest, responses((status = 200, body = AuthResponse)), security(("bearer" = [])))]
pub async fn update_profile(State(engine): State<AppState>, claims: Claims, Json(req): Json<UpdateProfileRequest>) -> ApiResult<AuthResponse> {
    if let Some(ref u) = req.username {
        if u.trim().is_empty() { return Err(err(StatusCode::BAD_REQUEST, "Username cannot be empty")); }
        if u.len() > 32 { return Err(err(StatusCode::BAD_REQUEST, "Username too long (max 32 chars)")); }
        if !u.chars().all(|c| c.is_alphanumeric() || c == '_' || c == '-') {
            return Err(err(StatusCode::BAD_REQUEST, "Username must be alphanumeric (underscores and hyphens allowed)"));
        }
        db::update_username(&engine.pool, claims.user_id, u).await
            .map_err(|e| if e.to_string().contains("already taken") { err(StatusCode::CONFLICT, "Username already taken") } else { internal(e) })?;
    }
    if let Some(ref p) = req.password {
        if p.len() < 8 { return Err(err(StatusCode::BAD_REQUEST, "Password must be at least 8 characters")); }
        if p.len() > 128 { return Err(err(StatusCode::BAD_REQUEST, "Password too long (max 128 chars)")); }
        if !p.chars().any(|c| c.is_uppercase()) { return Err(err(StatusCode::BAD_REQUEST, "Password must contain an uppercase letter")); }
        if !p.chars().any(|c| c.is_ascii_digit()) { return Err(err(StatusCode::BAD_REQUEST, "Password must contain a digit")); }
        let pw = p.clone();
        let hash = tokio::task::spawn_blocking(move || bcrypt::hash(&pw, 12))
            .await.map_err(internal)?.map_err(internal)?;
        db::update_user_password(&engine.pool, claims.user_id, &hash).await.map_err(internal)?;
    }
    let user = db::get_user(&engine.pool, claims.user_id).await.map_err(internal)?;
    let token = auth::create_token(user.id, &user.username, &user.role).map_err(internal)?;
    let refresh_token = auth::create_refresh_token(user.id, &user.username, &user.role).map_err(internal)?;
    Ok(Json(AuthResponse { token, refresh_token, user_id: user.id, username: user.username, role: user.role }))
}

// --- Admin ---

use super::*;


#[utoipa::path(put, path = "/api/profile", request_body = UpdateProfileRequest, responses((status = 200, body = AuthResponse)), security(("bearer" = [])))]
pub async fn update_profile(State(engine): State<AppState>, claims: Claims, Json(req): Json<UpdateProfileRequest>) -> ApiResult<AuthResponse> {
    if let Some(ref u) = req.username {
        validate_username(u)?;
        db::update_username(&engine.pool, claims.user_id, u).await
            .map_err(|e| if e.to_string().contains("already taken") { err(StatusCode::CONFLICT, "Username already taken") } else { internal(e) })?;
    }
    if let Some(ref p) = req.password {
        // V3: Require current password for password changes
        let current_pw = req.current_password.as_ref()
            .ok_or_else(|| err(StatusCode::BAD_REQUEST, "current_password is required to change password"))?;
        let user = db::get_user(&engine.pool, claims.user_id).await.map_err(internal)?;
        let hash_check = user.password_hash.clone();
        let pw_check = current_pw.clone();
        let valid = tokio::task::spawn_blocking(move || bcrypt::verify(&pw_check, &hash_check).unwrap_or(false))
            .await.map_err(internal)?;
        if !valid { return Err(err(StatusCode::FORBIDDEN, "Current password is incorrect")); }
        validate_password(p)?;
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

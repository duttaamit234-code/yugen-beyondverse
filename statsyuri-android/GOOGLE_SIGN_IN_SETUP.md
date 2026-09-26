# Google sign-in setup for StatsYuri

The Android UI and Credential Manager flow are included, but the repository intentionally does not contain an OAuth client ID or Firebase project secrets.

1. Open Google Auth Platform / Google Cloud Console.
2. Configure the OAuth consent screen for StatsYuri.
3. Create an OAuth 2.0 **Web application** client ID. Google requires the server/web client ID for the Sign in with Google request.
4. Replace the placeholder value in `app/src/main/res/values/strings.xml`:

```xml
<string name="default_web_client_id">YOUR_GOOGLE_WEB_CLIENT_ID.apps.googleusercontent.com</string>
```

5. For a real account backend, send the returned Google ID token to your server and validate it there before creating a session. Do not treat an unverified ID token as proof of identity.
6. If cloud data such as Google Drive is added later, request the specific Google authorization scope separately. Sign-in itself does not grant Drive access.

The current app stores the selected account's display name and email locally after a successful Google credential response. It does not upload datasets or silently request Google Drive access.

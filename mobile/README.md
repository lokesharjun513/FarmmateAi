# FarmMate AI Mobile

Flutter client for FarmMate AI.

## Push notifications (Firebase Cloud Messaging)

The app uses Firebase Installation ID (FID) registration through
`firebase_messaging`. Platform configuration is intentionally not committed.

### Android

1. Create a Firebase project and add an Android app with package name
   `com.example.mobile` (or the application ID you configure in
   `android/app/build.gradle.kts`).
2. Download `google-services.json` and place it at
   `android/app/google-services.json`.
3. Enable Cloud Messaging in the Firebase console.
4. Build and run. The Google Services Gradle plugin is applied only when that
   file exists, so builds without Firebase configuration still compile but push
   is disabled.

### iOS

1. Add an iOS app to the same Firebase project with bundle ID
   `com.example.mobile` (or your configured bundle identifier).
2. Download `GoogleService-Info.plist` and add it to the **Runner** target in
   Xcode, not only to the filesystem.
3. In Xcode, add the **Push Notifications** capability and enable
   **Background Modes → Remote notifications**. The repository already declares
   `UIBackgroundModes` in `Info.plist`, but the APNs entitlement must be created
   through Xcode signing.
4. Upload an APNs authentication key or certificate in Firebase Console →
   Project settings → Cloud Messaging.
5. Test on a real device. iOS simulators do not receive APNs notifications.

### Backend

The mobile app registers its FID with:

- `POST /api/v1/notifications/devices`
- `DELETE /api/v1/notifications/devices/{fid}`

The backend must be configured with Firebase Admin credentials as described in
`backend/README.md`.

### Runtime behavior

- Permission is requested after the first authenticated app frame.
- The FID is registered for the authenticated farmer and refreshed when Firebase
  rotates it.
- Logout removes the backend registration before the local auth token is
  cleared, and also unregisters the local FID.
- Foreground messages show an in-app SnackBar with an **Open** action.
- Notification taps route to `/dashboard` or `/ask-fm`; unknown routes and taps
  while signed out are ignored.
- Notification payloads should include `route` and/or `type` in `data` to
  control navigation.
- Background notification payloads are displayed by the operating system.
  Data-only background messages are not rendered locally.

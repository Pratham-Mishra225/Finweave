import { Stack } from "expo-router";
import { AuthProvider } from "../contexts/AuthContext";
import { DashboardProvider } from "../contexts/DashboardContext";

export default function RootLayout() {
  return (
    <AuthProvider>
      <DashboardProvider>
        <Stack initialRouteName="login">
          {/* Auth Screens */}
          <Stack.Screen name="login" options={{ headerShown: false }} />
          <Stack.Screen name="signup" options={{ headerShown: false }} />

          {/* Standalone Screens */}
          <Stack.Screen name="transactions" options={{ headerShown: false }} />
          <Stack.Screen name="notifications" options={{ headerShown: false }} />

          {/* Tabs folder auto-handled by Expo Router */}
          <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
          
          {/* Goals */}
          <Stack.Screen name="goals/add" options={{ headerShown: false }} />
        </Stack>
      </DashboardProvider>
    </AuthProvider>
  );
}

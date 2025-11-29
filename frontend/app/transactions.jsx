import { useRouter } from "expo-router";
import { useEffect } from "react";

/**
 * Redirect component for /transactions route
 * Redirects to the transactions tab in the main navigation
 */
export default function TransactionsRedirect() {
  const router = useRouter();
  
  useEffect(() => {
    // Redirect to the transactions tab
    router.replace("/(tabs)/transactions");
  }, [router]);
  
  return null;
}

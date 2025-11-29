import { Ionicons } from "@expo/vector-icons";
import { Tabs } from "expo-router";
import { View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

export default function TabsLayout() {
  return (
    <SafeAreaView style={{ flex: 1 }} edges={["bottom"]}>
      <View style={{ flex: 1, paddingBottom: 12 }}>
        <Tabs
          screenOptions={{
            headerShown: false,
            tabBarActiveTintColor: "#001F3F",
            tabBarInactiveTintColor: "gray",
            tabBarStyle: {
              height: 70,
              paddingBottom: 12,
              paddingTop: 6,
              elevation: 0,
              shadowOpacity: 0,
              borderTopWidth: 0,
              backgroundColor: "#FFFFFF",
            },
          }}
        >
          <Tabs.Screen
            name="home"
            options={{
              title: "Home",
              tabBarIcon: ({ color, size }) => (
                <Ionicons name="home-outline" size={size} color={color} />
              ),
            }}
          />

          <Tabs.Screen
            name="insights"
            options={{
              title: "Insights",
              tabBarIcon: ({ color, size }) => (
                <Ionicons name="analytics-outline" size={size} color={color} />
              ),
            }}
          />

          <Tabs.Screen
            name="goals"
            options={{
              title: "Goals",
              tabBarIcon: ({ color, size }) => (
                <Ionicons name="flag-outline" size={size} color={color} />
              ),
            }}
          />

          <Tabs.Screen
            name="transactions"
            options={{
              title: "Transactions",
              tabBarIcon: ({ color, size }) => (
                <Ionicons name="receipt-outline" size={size} color={color} />
              ),
            }}
          />

          <Tabs.Screen
            name="profile"
            options={{
              title: "Account",
              tabBarIcon: ({ color, size }) => (
                <Ionicons name="person-outline" size={size} color={color} />
              ),
            }}
          />
        </Tabs>
      </View>
    </SafeAreaView>
  );
}

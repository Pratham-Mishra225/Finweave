import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import { useState, useEffect, useCallback } from "react";
import {
  ActivityIndicator,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  useColorScheme,
  View,
} from "react-native";
import { useAuth } from "../contexts/AuthContext";

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL || "http://localhost:8000";

export default function Notifications() {
  const colorScheme = useColorScheme();
  const router = useRouter();
  const { idToken } = useAuth();
  const isDark = colorScheme === "dark";
  const [selectedFilter, setSelectedFilter] = useState("All");
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  const theme = {
    background: isDark ? "#0a0a0a" : "#F8F9FA",
    card: isDark ? "#1a1a1a" : "#FFFFFF",
    text: isDark ? "#FFFFFF" : "#001F3F",
    textSecondary: isDark ? "#A0A0A0" : "#6B7280",
    border: isDark ? "#2a2a2a" : "#E5E7EB",
    primary: "#001F3F",
    alert: "#FF9800",
    unreadDot: "#4CAF50",
  };

  const filters = ["All", "Transactions", "Goals", "Insights", "Alerts"];

  // Map filter names to backend filter values
  const getFilterValue = (filter) => {
    const filterMap = {
      "All": "all",
      "Transactions": "transactions",
      "Goals": "goals",
      "Insights": "insights",
      "Alerts": "alerts"
    };
    return filterMap[filter] || "all";
  };

  // Format relative time from date
  const formatRelativeTime = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays === 1) return "Yesterday";
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} week${Math.floor(diffDays / 7) > 1 ? 's' : ''} ago`;
    return date.toLocaleDateString();
  };

  // Get section name based on date
  const getSectionName = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    const weekAgo = new Date(today);
    weekAgo.setDate(weekAgo.getDate() - 7);

    if (date >= today) return "Today";
    if (date >= yesterday) return "Yesterday";
    if (date >= weekAgo) return "This Week";
    return "Earlier";
  };

  // Get icon based on notification type
  const getNotificationIcon = (type) => {
    const iconMap = {
      "transaction": "card-outline",
      "goal": "flag-outline",
      "insight": "analytics-outline",
      "alert": "warning-outline",
      "bill": "receipt-outline",
      "achievement": "trophy-outline",
      "system": "information-circle-outline"
    };
    return iconMap[type] || "notifications-outline";
  };

  // Fetch notifications from backend
  const fetchNotifications = useCallback(async (isRefresh = false) => {
    if (!idToken) {
      setLoading(false);
      return;
    }

    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    try {
      const filterValue = getFilterValue(selectedFilter);
      const response = await fetch(
        `${BACKEND_URL}/notifications?filter=${filterValue}&page=1&limit=50`,
        {
          headers: {
            Authorization: `Bearer ${idToken}`,
            "Content-Type": "application/json",
          },
        }
      );

      if (!response.ok) {
        throw new Error("Failed to fetch notifications");
      }

      const data = await response.json();
      
      // Transform and group notifications by section
      const groupedNotifications = groupNotificationsBySection(data.notifications || []);
      setNotifications(groupedNotifications);
      
      // Count unread
      const unread = (data.notifications || []).filter(n => !n.read).length;
      setUnreadCount(unread);
    } catch (error) {
      console.error("Error fetching notifications:", error);
      setNotifications([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [idToken, selectedFilter]);

  // Group notifications by section (Today, Yesterday, This Week, Earlier)
  const groupNotificationsBySection = (notificationsList) => {
    const sections = {
      "Today": [],
      "Yesterday": [],
      "This Week": [],
      "Earlier": []
    };

    notificationsList.forEach(notification => {
      const section = getSectionName(notification.created_at);
      const transformedNotification = {
        id: notification.id,
        type: notification.type,
        icon: getNotificationIcon(notification.type),
        title: notification.title,
        description: notification.message,
        time: formatRelativeTime(notification.created_at),
        unread: !notification.read,
        priority: notification.priority,
        metadata: notification.metadata
      };
      sections[section].push(transformedNotification);
    });

    // Convert to array format and filter out empty sections
    return Object.entries(sections)
      .filter(([_, data]) => data.length > 0)
      .map(([section, data]) => ({ section, data }));
  };

  // Mark notification as read
  const markAsRead = async (notificationId) => {
    if (!idToken) return;

    try {
      const response = await fetch(
        `${BACKEND_URL}/notifications/${notificationId}/mark-read`,
        {
          method: "PUT",
          headers: {
            Authorization: `Bearer ${idToken}`,
            "Content-Type": "application/json",
          },
        }
      );

      if (response.ok) {
        // Update local state
        setNotifications(prev => 
          prev.map(section => ({
            ...section,
            data: section.data.map(item => 
              item.id === notificationId ? { ...item, unread: false } : item
            )
          }))
        );
        setUnreadCount(prev => Math.max(0, prev - 1));
      }
    } catch (error) {
      console.error("Error marking notification as read:", error);
    }
  };

  // Mark all as read
  const markAllAsRead = async () => {
    if (!idToken) return;

    try {
      const response = await fetch(
        `${BACKEND_URL}/notifications/mark-all-read`,
        {
          method: "PUT",
          headers: {
            Authorization: `Bearer ${idToken}`,
            "Content-Type": "application/json",
          },
        }
      );

      if (response.ok) {
        // Update local state
        setNotifications(prev => 
          prev.map(section => ({
            ...section,
            data: section.data.map(item => ({ ...item, unread: false }))
          }))
        );
        setUnreadCount(0);
      }
    } catch (error) {
      console.error("Error marking all notifications as read:", error);
    }
  };

  // Fetch notifications on mount and when filter changes
  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  // Handle filter change
  const handleFilterChange = (filter) => {
    setSelectedFilter(filter);
  };

  const onRefresh = () => {
    fetchNotifications(true);
  };

  const getIconColor = (type) => {
    switch (type) {
      case "transaction":
        return theme.primary;
      case "goal":
        return "#4CAF50";
      case "insight":
        return "#2196F3";
      case "alert":
        return theme.alert;
      default:
        return theme.textSecondary;
    }
  };

  const renderNotification = (item) => (
    <TouchableOpacity
      key={item.id}
      style={styles.notificationItem}
      activeOpacity={0.7}
      onPress={() => item.unread && markAsRead(item.id)}
    >
      <View style={styles.notificationContent}>
        <View
          style={[
            styles.notificationIcon,
            { backgroundColor: isDark ? "#2a2a2a" : "#F8F9FA" },
          ]}
        >
          <Ionicons
            name={item.icon}
            size={22}
            color={getIconColor(item.type)}
          />
        </View>
        <View style={styles.notificationDetails}>
          <View style={styles.notificationHeader}>
            <Text
              style={[
                styles.notificationTitle,
                { color: theme.text },
                item.unread && styles.notificationTitleUnread,
              ]}
            >
              {item.title}
            </Text>
            {item.unread && (
              <View
                style={[styles.unreadDot, { backgroundColor: theme.unreadDot }]}
              />
            )}
          </View>
          <Text
            style={[
              styles.notificationDescription,
              { color: theme.textSecondary },
            ]}
            numberOfLines={2}
          >
            {item.description}
          </Text>
          <Text
            style={[styles.notificationTime, { color: theme.textSecondary }]}
          >
            {item.time}
          </Text>
        </View>
      </View>
    </TouchableOpacity>
  );

  // Render empty state
  const renderEmptyState = () => (
    <View style={styles.emptyContainer}>
      <Ionicons
        name="notifications-off-outline"
        size={64}
        color={theme.textSecondary}
      />
      <Text style={[styles.emptyTitle, { color: theme.text }]}>
        No notifications yet
      </Text>
      <Text style={[styles.emptySubtitle, { color: theme.textSecondary }]}>
        {selectedFilter === "All" 
          ? "You're all caught up! Check back later."
          : `No ${selectedFilter.toLowerCase()} notifications found.`}
      </Text>
    </View>
  );

  // Render loading state
  const renderLoadingState = () => (
    <View style={styles.loadingContainer}>
      <ActivityIndicator size="large" color={theme.primary} />
      <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
        Loading notifications...
      </Text>
    </View>
  );

  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      <View style={styles.header}>
        <TouchableOpacity
          onPress={() => router.back()}
          style={styles.backButton}
        >
          <Ionicons name="arrow-back" size={24} color={theme.text} />
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <Text style={[styles.headerTitle, { color: theme.text }]}>
            Notifications
          </Text>
          <Text style={[styles.headerSubtitle, { color: theme.textSecondary }]}>
            {unreadCount > 0 
              ? `${unreadCount} unread notification${unreadCount > 1 ? 's' : ''}`
              : 'Stay updated with your activity'}
          </Text>
        </View>
        {unreadCount > 0 ? (
          <TouchableOpacity
            style={[
              styles.markAllReadButton,
              { backgroundColor: isDark ? "#2a2a2a" : "#F0F1F3" },
            ]}
            onPress={markAllAsRead}
          >
            <Ionicons
              name="checkmark-done-outline"
              size={20}
              color={theme.primary}
            />
          </TouchableOpacity>
        ) : (
          <View
            style={[
              styles.headerIcon,
              { backgroundColor: isDark ? "#2a2a2a" : "#F0F1F3" },
            ]}
          >
            <Ionicons
              name="notifications-outline"
              size={24}
              color={theme.primary}
            />
          </View>
        )}
      </View>

      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.filtersContainer}
      >
        {filters.map((filter) => (
          <TouchableOpacity
            key={filter}
            style={[
              styles.filterChip,
              {
                borderColor:
                  selectedFilter === filter ? theme.primary : theme.border,
                backgroundColor:
                  selectedFilter === filter ? theme.primary : theme.card,
              },
            ]}
            onPress={() => handleFilterChange(filter)}
            activeOpacity={0.7}
          >
            <Text
              style={[
                styles.filterText,
                {
                  color: selectedFilter === filter ? "#FFFFFF" : theme.text,
                },
              ]}
            >
              {filter}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {loading ? (
        renderLoadingState()
      ) : notifications.length === 0 ? (
        renderEmptyState()
      ) : (
        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={onRefresh}
              tintColor={theme.primary}
              colors={[theme.primary]}
            />
          }
        >
          {notifications.map((section) => (
            <View key={section.section} style={styles.section}>
              <Text style={[styles.sectionTitle, { color: theme.textSecondary }]}>
                {section.section}
              </Text>
              <View
                style={[
                  styles.notificationCard,
                  { backgroundColor: theme.card, borderColor: theme.border },
                ]}
              >
                {section.data.map((item, index) => (
                  <View key={item.id}>
                    {renderNotification(item)}
                    {index < section.data.length - 1 && (
                      <View
                        style={[
                          styles.divider,
                          { backgroundColor: theme.border },
                        ]}
                      />
                    )}
                  </View>
                ))}
              </View>
            </View>
          ))}
          <View style={styles.bottomPadding} />
        </ScrollView>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 16,
  },
  backButton: {
    width: 40,
    height: 40,
    alignItems: "center",
    justifyContent: "center",
  },
  headerCenter: {
    flex: 1,
    marginLeft: 8,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: "700",
    letterSpacing: -0.5,
  },
  headerSubtitle: {
    fontSize: 13,
    fontWeight: "400",
    marginTop: 2,
  },
  headerIcon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: "center",
    justifyContent: "center",
  },
  markAllReadButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: "center",
    justifyContent: "center",
  },
  filtersContainer: {
    paddingHorizontal: 20,
    paddingBottom: 10,
    flexDirection: "row",
    alignItems: "center",
    height: 60,
  },
  filterChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    marginRight: 8,
    flexShrink: 1,
  },

  filterText: {
    fontSize: 14,
    fontWeight: "500",
  },
  scrollView: {
    paddingTop: 20,
  },
  scrollContent: {
    paddingHorizontal: 20,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 12,
    fontWeight: "600",
    letterSpacing: 1,
    marginBottom: 12,
    textTransform: "uppercase",
  },
  notificationCard: {
    borderRadius: 16,
    borderWidth: 1,
    overflow: "hidden",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 3,
  },
  notificationItem: {
    paddingVertical: 16,
    paddingHorizontal: 16,
  },
  notificationContent: {
    flexDirection: "row",
  },
  notificationIcon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: "center",
    justifyContent: "center",
    marginRight: 12,
  },
  notificationDetails: {
    flex: 1,
  },
  notificationHeader: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 6,
  },
  notificationTitle: {
    fontSize: 15,
    fontWeight: "600",
    flex: 1,
  },
  notificationTitleUnread: {
    fontWeight: "700",
  },
  unreadDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginLeft: 8,
  },
  notificationDescription: {
    fontSize: 14,
    fontWeight: "400",
    lineHeight: 20,
    marginBottom: 6,
  },
  notificationTime: {
    fontSize: 12,
    fontWeight: "400",
  },
  divider: {
    height: 1,
    marginHorizontal: 16,
  },
  bottomPadding: {
    height: 40,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingTop: 100,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 14,
    fontWeight: "500",
  },
  emptyContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingTop: 100,
    paddingHorizontal: 40,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: "600",
    marginTop: 16,
    textAlign: "center",
  },
  emptySubtitle: {
    fontSize: 14,
    fontWeight: "400",
    marginTop: 8,
    textAlign: "center",
    lineHeight: 20,
  },
});

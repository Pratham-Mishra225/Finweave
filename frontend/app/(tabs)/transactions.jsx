import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import { useState, useEffect, useCallback } from "react";
import {
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  useColorScheme,
  View,
  ActivityIndicator,
  Modal,
  Alert,
  Platform,
  RefreshControl,
} from "react-native";
import { useAuth } from "../../contexts/AuthContext";
import { useDashboard } from "../../contexts/DashboardContext";
import DateTimePicker from '@react-native-community/datetimepicker';

export default function Transactions() {
  const colorScheme = useColorScheme();
  const router = useRouter();
  const { idToken } = useAuth();
  const { refreshDashboard, applyLocalTransaction } = useDashboard();
  const isDark = colorScheme === "dark";
  
  const [selectedFilter, setSelectedFilter] = useState("All");
  const [searchQuery, setSearchQuery] = useState("");
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [addModalVisible, setAddModalVisible] = useState(false);

  // Form state for adding transaction
  const [formData, setFormData] = useState({
    name: "",
    amount: "",
    type: "expense",
    category: "Food",
    description: "",
    date: new Date(),
  });
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const theme = {
    background: isDark ? "#0a0a0a" : "#F8F9FA",
    card: isDark ? "#1a1a1a" : "#FFFFFF",
    text: isDark ? "#FFFFFF" : "#001F3F",
    textSecondary: isDark ? "#A0A0A0" : "#6B7280",
    border: isDark ? "#2a2a2a" : "#E5E7EB",
    primary: "#001F3F",
    income: "#4CAF50",
    expense: "#EF4444",
    searchBg: isDark ? "#1a1a1a" : "#F3F4F6",
    modalBg: isDark ? "#1a1a1a" : "#FFFFFF",
    inputBg: isDark ? "#2a2a2a" : "#F3F4F6",
  };

  const filters = [
    "All",
    "Food",
    "Bills",
    "Shopping",
    "Travel",
    "Subscriptions",
    "Salary",
    "Freelance",
    "Investment",
    "Others",
  ];

  const categories = [
    { value: "Food", icon: "restaurant-outline" },
    { value: "Bills", icon: "flash-outline" },
    { value: "Shopping", icon: "cart-outline" },
    { value: "Travel", icon: "car-outline" },
    { value: "Subscriptions", icon: "play-circle-outline" },
    { value: "Salary", icon: "cash-outline" },
    { value: "Freelance", icon: "briefcase-outline" },
    { value: "Investment", icon: "trending-up-outline" },
    { value: "Others", icon: "ellipsis-horizontal-outline" },
  ];

  const API_BASE_URL = process.env.EXPO_PUBLIC_BACKEND_URL || "http://localhost:8000";

  const fetchTransactions = useCallback(async (pageNum = 1, isRefresh = false) => {
    if (!idToken) return;

    try {
      if (isRefresh) {
        setRefreshing(true);
      } else if (pageNum === 1) {
        setLoading(true);
      }

      let url = `${API_BASE_URL}/transactions?page=${pageNum}&limit=20`;
      
      // Apply filter if not "All"
      if (selectedFilter !== "All") {
        url = `${API_BASE_URL}/transactions/filter?category=${selectedFilter}&page=${pageNum}&limit=20`;
      }

      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${idToken}`,
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Failed to fetch transactions");
      }

      const data = await response.json();
      
      if (pageNum === 1 || isRefresh) {
        setTransactions(data.transactions);
      } else {
        setTransactions((prev) => [...prev, ...data.transactions]);
      }
      
    } catch (error) {
      console.error("Error fetching transactions:", error);
      Alert.alert("Error", "Failed to load transactions");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [API_BASE_URL, idToken, selectedFilter]);

  useEffect(() => {
    if (!idToken) return;
    fetchTransactions();
  }, [fetchTransactions, idToken]);

  const searchTransactions = async (query) => {
    if (!idToken || !query.trim()) {
      fetchTransactions();
      return;
    }

    try {
      setLoading(true);
      const response = await fetch(
        `${API_BASE_URL}/transactions/search?q=${encodeURIComponent(query)}&page=1&limit=20`,
        {
          headers: {
            Authorization: `Bearer ${idToken}`,
            "Content-Type": "application/json",
          },
        }
      );

      if (!response.ok) {
        throw new Error("Search failed");
      }

      const data = await response.json();
      setTransactions(data.transactions);
    } catch (error) {
      console.error("Error searching transactions:", error);
      Alert.alert("Error", "Search failed");
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (text) => {
    setSearchQuery(text);
    if (text.trim().length > 2) {
      searchTransactions(text);
    } else if (text.trim().length === 0) {
      fetchTransactions();
    }
  };

  const handleAddTransaction = async () => {
    if (!formData.name.trim() || !formData.amount || parseFloat(formData.amount) <= 0) {
      Alert.alert("Error", "Please fill in all required fields with valid values");
      return;
    }

    try {
      setSubmitting(true);
      const response = await fetch(`${API_BASE_URL}/transactions`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${idToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: formData.name.trim(),
          amount: parseFloat(formData.amount),
          type: formData.type,
          category: formData.category,
          description: formData.description.trim() || null,
          date: formData.date.toISOString(),
          recurring: false,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to add transaction");
      }

      const createdTransaction = await response.json();
      applyLocalTransaction(createdTransaction, "add");
      refreshDashboard({ silent: true }).catch(() => {});

      Alert.alert("Success", "Transaction added successfully");
      setAddModalVisible(false);
      resetForm();
      fetchTransactions(1, true);
    } catch (error) {
      console.error("Error adding transaction:", error);
      Alert.alert("Error", "Failed to add transaction");
    } finally {
      setSubmitting(false);
    }
  };

  const resetForm = () => {
    setFormData({
      name: "",
      amount: "",
      type: "expense",
      category: "Food",
      description: "",
      date: new Date(),
    });
  };

  const getCategoryIcon = (category) => {
    const cat = categories.find((c) => c.value === category);
    return cat ? cat.icon : "ellipsis-horizontal-outline";
  };

  const groupTransactionsByDate = (transactions) => {
    const grouped = {};
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const thisWeek = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
    const lastWeek = new Date(today.getTime() - 14 * 24 * 60 * 60 * 1000);

    transactions.forEach((transaction) => {
      const transactionDate = new Date(transaction.date);
      let section;

      if (transactionDate >= today) {
        section = "Today";
      } else if (transactionDate >= thisWeek) {
        section = "This Week";
      } else if (transactionDate >= lastWeek) {
        section = "Last Week";
      } else {
        section = "Earlier";
      }

      if (!grouped[section]) {
        grouped[section] = [];
      }
      grouped[section].push(transaction);
    });

    return Object.entries(grouped).map(([section, data]) => ({
      section,
      data,
    }));
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const renderTransaction = (item) => (
    <TouchableOpacity
      key={item.id}
      style={styles.transactionItem}
      activeOpacity={0.7}
    >
      <View
        style={[
          styles.transactionIcon,
          { backgroundColor: isDark ? "#2a2a2a" : "#F8F9FA" },
        ]}
      >
        <Ionicons
          name={getCategoryIcon(item.category)}
          size={20}
          color={item.type === "income" ? theme.income : theme.primary}
        />
      </View>
      <View style={styles.transactionDetails}>
        <Text style={[styles.transactionName, { color: theme.text }]}>
          {item.name}
        </Text>
        <View style={styles.transactionMeta}>
          <Text
            style={[styles.transactionCategory, { color: theme.textSecondary }]}
          >
            {item.category}
          </Text>
          <Text
            style={[styles.transactionDate, { color: theme.textSecondary }]}
          >
            {" • "}
            {formatDate(item.date)}
          </Text>
        </View>
      </View>
      <Text
        style={[
          styles.transactionAmount,
          {
            color: item.type === "income" ? theme.income : theme.text,
          },
        ]}
      >
        {item.type === "income" ? "+" : "-"}₹{Math.abs(item.amount).toLocaleString()}
      </Text>
    </TouchableOpacity>
  );

  const renderEmptyState = () => (
    <View style={styles.emptyState}>
      <Ionicons name="receipt-outline" size={64} color={theme.textSecondary} />
      <Text style={[styles.emptyText, { color: theme.text }]}>
        No transactions yet
      </Text>
      <Text style={[styles.emptySubtext, { color: theme.textSecondary }]}>
        Add your first transaction to get started
      </Text>
    </View>
  );

  const groupedTransactions = groupTransactionsByDate(transactions);

  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      <View style={styles.header}>
        <View style={styles.headerCenter}>
          <Text style={[styles.headerTitle, { color: theme.text }]}>
            Transactions
          </Text>
          <Text style={[styles.headerSubtitle, { color: theme.textSecondary }]}>
            Your complete financial history
          </Text>
        </View>
        <TouchableOpacity
          onPress={() => setAddModalVisible(true)}
          style={[
            styles.headerIcon,
            { backgroundColor: theme.primary },
          ]}
        >
          <Ionicons name="add" size={24} color="#FFFFFF" />
        </TouchableOpacity>
      </View>

      <View style={styles.searchContainer}>
        <View style={[styles.searchBar, { backgroundColor: theme.searchBg }]}>
          <Ionicons
            name="search-outline"
            size={20}
            color={theme.textSecondary}
          />
          <TextInput
            style={[styles.searchInput, { color: theme.text }]}
            placeholder="Search transactions…"
            placeholderTextColor={theme.textSecondary}
            value={searchQuery}
            onChangeText={handleSearch}
          />
          {searchQuery.length > 0 && (
            <TouchableOpacity onPress={() => handleSearch("")}>
              <Ionicons name="close-circle" size={20} color={theme.textSecondary} />
            </TouchableOpacity>
          )}
        </View>
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
              selectedFilter === filter && { backgroundColor: theme.primary },
              {
                borderColor:
                  selectedFilter === filter ? theme.primary : theme.border,
                backgroundColor:
                  selectedFilter === filter ? theme.primary : theme.card,
              },
            ]}
            onPress={() => setSelectedFilter(filter)}
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
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.primary} />
        </View>
      ) : transactions.length === 0 ? (
        renderEmptyState()
      ) : (
        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={{
            ...styles.scrollContent,
            flexGrow: 1,
            paddingBottom: 40,
          }}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={() => fetchTransactions(1, true)}
              tintColor={theme.primary}
            />
          }
        >
          {groupedTransactions.map((section) => (
            <View key={section.section} style={styles.section}>
              <Text style={[styles.sectionTitle, { color: theme.textSecondary }]}>
                {section.section}
              </Text>
              <View
                style={[
                  styles.transactionCard,
                  { backgroundColor: theme.card, borderColor: theme.border },
                ]}
              >
                {section.data.map((item, index) => (
                  <View key={item.id}>
                    {renderTransaction(item)}
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
        </ScrollView>
      )}

      {/* Add Transaction Modal */}
      <Modal
        visible={addModalVisible}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setAddModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={[styles.modalContent, { backgroundColor: theme.modalBg }]}>
            <View style={styles.modalHeader}>
              <Text style={[styles.modalTitle, { color: theme.text }]}>
                Add Transaction
              </Text>
              <TouchableOpacity onPress={() => setAddModalVisible(false)}>
                <Ionicons name="close" size={24} color={theme.text} />
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.modalScroll}>
              {/* Transaction Type Toggle */}
              <View style={styles.typeToggleContainer}>
                <TouchableOpacity
                  style={[
                    styles.typeToggle,
                    formData.type === "expense" && {
                      backgroundColor: theme.expense,
                    },
                    { borderColor: theme.border },
                  ]}
                  onPress={() => setFormData({ ...formData, type: "expense" })}
                >
                  <Text
                    style={[
                      styles.typeToggleText,
                      { color: formData.type === "expense" ? "#FFFFFF" : theme.text },
                    ]}
                  >
                    Expense
                  </Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[
                    styles.typeToggle,
                    formData.type === "income" && {
                      backgroundColor: theme.income,
                    },
                    { borderColor: theme.border },
                  ]}
                  onPress={() => setFormData({ ...formData, type: "income" })}
                >
                  <Text
                    style={[
                      styles.typeToggleText,
                      { color: formData.type === "income" ? "#FFFFFF" : theme.text },
                    ]}
                  >
                    Income
                  </Text>
                </TouchableOpacity>
              </View>

              {/* Transaction Name */}
              <View style={styles.inputGroup}>
                <Text style={[styles.inputLabel, { color: theme.textSecondary }]}>
                  Name *
                </Text>
                <TextInput
                  style={[
                    styles.input,
                    { backgroundColor: theme.inputBg, color: theme.text },
                  ]}
                  placeholder="e.g., Grocery Shopping"
                  placeholderTextColor={theme.textSecondary}
                  value={formData.name}
                  onChangeText={(text) => setFormData({ ...formData, name: text })}
                />
              </View>

              {/* Amount */}
              <View style={styles.inputGroup}>
                <Text style={[styles.inputLabel, { color: theme.textSecondary }]}>
                  Amount *
                </Text>
                <TextInput
                  style={[
                    styles.input,
                    { backgroundColor: theme.inputBg, color: theme.text },
                  ]}
                  placeholder="0.00"
                  placeholderTextColor={theme.textSecondary}
                  keyboardType="decimal-pad"
                  value={formData.amount}
                  onChangeText={(text) => setFormData({ ...formData, amount: text })}
                />
              </View>

              {/* Category */}
              <View style={styles.inputGroup}>
                <Text style={[styles.inputLabel, { color: theme.textSecondary }]}>
                  Category
                </Text>
                <ScrollView
                  horizontal
                  showsHorizontalScrollIndicator={false}
                  contentContainerStyle={styles.categoriesScroll}
                >
                  {categories.map((cat) => (
                    <TouchableOpacity
                      key={cat.value}
                      style={[
                        styles.categoryChip,
                        formData.category === cat.value && {
                          backgroundColor: theme.primary,
                        },
                        { borderColor: theme.border },
                      ]}
                      onPress={() =>
                        setFormData({ ...formData, category: cat.value })
                      }
                    >
                      <Ionicons
                        name={cat.icon}
                        size={16}
                        color={
                          formData.category === cat.value ? "#FFFFFF" : theme.text
                        }
                      />
                      <Text
                        style={[
                          styles.categoryChipText,
                          {
                            color:
                              formData.category === cat.value
                                ? "#FFFFFF"
                                : theme.text,
                          },
                        ]}
                      >
                        {cat.value}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </ScrollView>
              </View>

              {/* Date */}
              <View style={styles.inputGroup}>
                <Text style={[styles.inputLabel, { color: theme.textSecondary }]}>
                  Date
                </Text>
                <TouchableOpacity
                  style={[
                    styles.input,
                    { backgroundColor: theme.inputBg, justifyContent: "center" },
                  ]}
                  onPress={() => setShowDatePicker(true)}
                >
                  <Text style={{ color: theme.text }}>
                    {formData.date.toLocaleDateString()}
                  </Text>
                </TouchableOpacity>
                {showDatePicker && (
                  <DateTimePicker
                    value={formData.date}
                    mode="date"
                    display="default"
                    onChange={(event, selectedDate) => {
                      setShowDatePicker(Platform.OS === "ios");
                      if (selectedDate) {
                        setFormData({ ...formData, date: selectedDate });
                      }
                    }}
                  />
                )}
              </View>

              {/* Description */}
              <View style={styles.inputGroup}>
                <Text style={[styles.inputLabel, { color: theme.textSecondary }]}>
                  Description (Optional)
                </Text>
                <TextInput
                  style={[
                    styles.input,
                    styles.textArea,
                    { backgroundColor: theme.inputBg, color: theme.text },
                  ]}
                  placeholder="Add notes..."
                  placeholderTextColor={theme.textSecondary}
                  multiline
                  numberOfLines={3}
                  value={formData.description}
                  onChangeText={(text) =>
                    setFormData({ ...formData, description: text })
                  }
                />
              </View>

              {/* Submit Button */}
              <TouchableOpacity
                style={[
                  styles.submitButton,
                  { backgroundColor: theme.primary },
                  submitting && { opacity: 0.6 },
                ]}
                onPress={handleAddTransaction}
                disabled={submitting}
              >
                {submitting ? (
                  <ActivityIndicator color="#FFFFFF" />
                ) : (
                  <Text style={styles.submitButtonText}>Add Transaction</Text>
                )}
              </TouchableOpacity>
            </ScrollView>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 16,
  },
  headerCenter: { flex: 1 },
  headerTitle: { fontSize: 24, fontWeight: "700", letterSpacing: -0.5 },
  headerSubtitle: { fontSize: 13, marginTop: 2 },
  headerIcon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: "center",
    justifyContent: "center",
  },
  searchContainer: { paddingHorizontal: 20, marginBottom: 16 },
  searchBar: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    height: 48,
    borderRadius: 12,
  },
  searchInput: { flex: 1, marginLeft: 12, fontSize: 15 },
  filtersContainer: { paddingHorizontal: 20, paddingBottom: 16, gap: 8 },
  filterChip: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    borderWidth: 1,
    marginRight: 8,
  },
  filterText: { fontSize: 14, fontWeight: "500" },
  scrollView: { flex: 1 },
  scrollContent: { paddingHorizontal: 20 },
  section: { marginBottom: 24 },
  sectionTitle: {
    fontSize: 12,
    fontWeight: "600",
    letterSpacing: 1,
    marginBottom: 12,
    textTransform: "uppercase",
  },
  transactionCard: {
    borderRadius: 16,
    borderWidth: 1,
    overflow: "hidden",
  },
  transactionItem: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 14,
    paddingHorizontal: 16,
  },
  transactionIcon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: "center",
    justifyContent: "center",
    marginRight: 12,
  },
  transactionDetails: { flex: 1 },
  transactionName: { fontSize: 15, fontWeight: "600", marginBottom: 4 },
  transactionMeta: { flexDirection: "row", alignItems: "center" },
  transactionCategory: { fontSize: 13 },
  transactionDate: { fontSize: 13 },
  transactionAmount: { fontSize: 16, fontWeight: "700", marginLeft: 12 },
  divider: { height: 1, marginHorizontal: 16 },
  loadingContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  emptyState: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 40,
  },
  emptyText: {
    fontSize: 20,
    fontWeight: "600",
    marginTop: 16,
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    textAlign: "center",
  },
  // Modal Styles
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0, 0, 0, 0.5)",
    justifyContent: "flex-end",
  },
  modalContent: {
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    paddingTop: 20,
    paddingBottom: 40,
    maxHeight: "90%",
  },
  modalHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  modalTitle: {
    fontSize: 24,
    fontWeight: "700",
  },
  modalScroll: {
    paddingHorizontal: 20,
  },
  typeToggleContainer: {
    flexDirection: "row",
    gap: 12,
    marginBottom: 24,
  },
  typeToggle: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 12,
    borderWidth: 1,
    alignItems: "center",
  },
  typeToggleText: {
    fontSize: 16,
    fontWeight: "600",
  },
  inputGroup: {
    marginBottom: 20,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: "600",
    marginBottom: 8,
  },
  input: {
    height: 50,
    borderRadius: 12,
    paddingHorizontal: 16,
    fontSize: 15,
  },
  textArea: {
    height: 100,
    paddingTop: 12,
    textAlignVertical: "top",
  },
  categoriesScroll: {
    gap: 8,
  },
  categoryChip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 20,
    borderWidth: 1,
  },
  categoryChipText: {
    fontSize: 13,
    fontWeight: "500",
  },
  submitButton: {
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: "center",
    marginTop: 10,
  },
  submitButtonText: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "600",
  },
});

import React, { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  useColorScheme,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  Alert,
  ActivityIndicator,
} from "react-native";
import { useRouter } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import DateTimePicker from "@react-native-community/datetimepicker";
import { useAuth } from "../../contexts/AuthContext";

const API_BASE_URL = process.env.EXPO_PUBLIC_BACKEND_URL || "http://localhost:8000";

export default function AddGoal() {
  const colorScheme = useColorScheme();
  const router = useRouter();
  const { idToken } = useAuth();
  const isDark = colorScheme === "dark";

  const [goalTitle, setGoalTitle] = useState("");
  const [targetAmount, setTargetAmount] = useState("");
  const [savedAmount, setSavedAmount] = useState("");
  const [deadline, setDeadline] = useState(null);
  const [description, setDescription] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("");
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState({});

  const theme = {
    background: isDark ? "#0a0a0a" : "#F8F9FA",
    card: isDark ? "#1a1a1a" : "#FFFFFF",
    text: isDark ? "#FFFFFF" : "#001F3F",
    textSecondary: isDark ? "#A0A0A0" : "#6B7280",
    border: isDark ? "#2a2a2a" : "#E5E7EB",
    input: isDark ? "#2a2a2a" : "#FFFFFF",
    inputBorder: isDark ? "#3a3a3a" : "#E5E7EB",
    primary: "#001F3F",
    error: "#EF4444",
  };

  // Categories matching backend GoalCategory enum
  const categories = [
    {
      id: "Savings",
      label: "Savings",
      icon: "wallet-outline",
      color: "#4CAF50",
    },
    {
      id: "Investment",
      label: "Investment",
      icon: "trending-up-outline",
      color: "#2196F3",
    },
    {
      id: "Purchase",
      label: "Purchase",
      icon: "cart-outline",
      color: "#FF9800",
    },
    {
      id: "Travel",
      label: "Travel",
      icon: "airplane-outline",
      color: "#00BCD4",
    },
    {
      id: "Education",
      label: "Education",
      icon: "school-outline",
      color: "#9C27B0",
    },
    {
      id: "Emergency",
      label: "Emergency",
      icon: "shield-checkmark-outline",
      color: "#F44336",
    },
    {
      id: "Debt",
      label: "Debt",
      icon: "card-outline",
      color: "#795548",
    },
    {
      id: "Other",
      label: "Other",
      icon: "ellipsis-horizontal-outline",
      color: "#607D8B",
    },
  ];

  const validateForm = () => {
    const newErrors = {};

    if (!goalTitle.trim()) {
      newErrors.title = "Goal title is required";
    }

    if (!targetAmount || isNaN(Number(targetAmount)) || Number(targetAmount) <= 0) {
      newErrors.targetAmount = "Please enter a valid target amount";
    }

    if (savedAmount && (isNaN(Number(savedAmount)) || Number(savedAmount) < 0)) {
      newErrors.savedAmount = "Please enter a valid amount";
    }

    if (savedAmount && targetAmount && Number(savedAmount) > Number(targetAmount)) {
      newErrors.savedAmount = "Saved amount cannot exceed target amount";
    }

    if (!selectedCategory) {
      newErrors.category = "Please select a category";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleDateChange = (event, selectedDate) => {
    setShowDatePicker(Platform.OS === "ios");
    if (selectedDate) {
      setDeadline(selectedDate);
    }
  };

  const formatDate = (date) => {
    if (!date) return "";
    return date.toISOString().split("T")[0];
  };

  const handleSave = async () => {
    if (!validateForm()) {
      return;
    }

    if (!idToken) {
      Alert.alert("Error", "Please log in to create a goal");
      return;
    }

    try {
      setSubmitting(true);

      const goalData = {
        title: goalTitle.trim(),
        target_amount: Number(targetAmount),
        saved_amount: savedAmount ? Number(savedAmount) : 0,
        category: selectedCategory,
        description: description.trim() || null,
        deadline: deadline ? formatDate(deadline) : null,
      };

      const response = await fetch(`${API_BASE_URL}/goals`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${idToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(goalData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to create goal");
      }

      Alert.alert("Success", "Goal created successfully!", [
        { text: "OK", onPress: () => router.back() },
      ]);
    } catch (err) {
      console.error("Error creating goal:", err);
      Alert.alert("Error", err.message || "Failed to create goal");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === "ios" ? "padding" : "height"}
      style={[styles.container, { backgroundColor: theme.background }]}
    >
      <View style={styles.header}>
        <TouchableOpacity
          onPress={() => router.back()}
          style={styles.backButton}
        >
          <Ionicons name="arrow-back" size={24} color={theme.text} />
        </TouchableOpacity>

        <View style={styles.headerCenter}>
          <Text style={[styles.headerTitle, { color: theme.text }]}>
            Add Goal
          </Text>
          <Text style={[styles.headerSubtitle, { color: theme.textSecondary }]}>
            Create a new financial goal
          </Text>
        </View>
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
      >
        {/* Goal Title */}
        <View style={styles.formSection}>
          <Text style={[styles.label, { color: theme.text }]}>Goal Title *</Text>
          <View
            style={[
              styles.inputWrapper,
              { 
                backgroundColor: theme.input, 
                borderColor: errors.title ? theme.error : theme.inputBorder 
              },
            ]}
          >
            <Ionicons
              name="flag-outline"
              size={20}
              color={theme.textSecondary}
              style={styles.inputIcon}
            />
            <TextInput
              style={[styles.input, { color: theme.text }]}
              placeholder="e.g., Emergency Fund"
              placeholderTextColor={theme.textSecondary}
              value={goalTitle}
              onChangeText={(text) => {
                setGoalTitle(text);
                if (errors.title) setErrors({ ...errors, title: null });
              }}
            />
          </View>
          {errors.title && (
            <Text style={[styles.errorText, { color: theme.error }]}>
              {errors.title}
            </Text>
          )}
        </View>

        {/* Target Amount */}
        <View style={styles.formSection}>
          <Text style={[styles.label, { color: theme.text }]}>
            Target Amount *
          </Text>
          <View
            style={[
              styles.inputWrapper,
              { 
                backgroundColor: theme.input, 
                borderColor: errors.targetAmount ? theme.error : theme.inputBorder 
              },
            ]}
          >
            <Ionicons
              name="cash-outline"
              size={20}
              color={theme.textSecondary}
              style={styles.inputIcon}
            />
            <Text
              style={[styles.currencySymbol, { color: theme.textSecondary }]}
            >
              ₹
            </Text>
            <TextInput
              style={[styles.input, { color: theme.text }]}
              placeholder="50,000"
              placeholderTextColor={theme.textSecondary}
              value={targetAmount}
              onChangeText={(text) => {
                // Allow only digits and a single decimal point
                let cleaned = text.replace(/[^0-9.]/g, "");
                const parts = cleaned.split(".");
                if (parts.length > 1) {
                  cleaned = parts[0] + "." + parts.slice(1).join("");
                }
                setTargetAmount(cleaned);
                if (errors.targetAmount) setErrors({ ...errors, targetAmount: null });
              }}
              keyboardType="numeric"
            />
          </View>
          {errors.targetAmount && (
            <Text style={[styles.errorText, { color: theme.error }]}>
              {errors.targetAmount}
            </Text>
          )}
        </View>

        {/* Initial Saved Amount (Optional) */}
        <View style={styles.formSection}>
          <Text style={[styles.label, { color: theme.text }]}>
            Initial Savings (Optional)
          </Text>
          <View
            style={[
              styles.inputWrapper,
              { 
                backgroundColor: theme.input, 
                borderColor: errors.savedAmount ? theme.error : theme.inputBorder 
              },
            ]}
          >
            <Ionicons
              name="wallet-outline"
              size={20}
              color={theme.textSecondary}
              style={styles.inputIcon}
            />
            <Text
              style={[styles.currencySymbol, { color: theme.textSecondary }]}
            >
              ₹
            </Text>
            <TextInput
              style={[styles.input, { color: theme.text }]}
              placeholder="0"
              placeholderTextColor={theme.textSecondary}
              value={savedAmount}
              onChangeText={(text) => {
                // Remove all non-digit and non-decimal characters
                let sanitized = text.replace(/[^0-9.]/g, "");
                // Allow only one decimal point
                const parts = sanitized.split(".");
                if (parts.length > 1) {
                  sanitized = parts[0] + "." + parts.slice(1).join("");
                }
                setSavedAmount(sanitized);
                if (errors.savedAmount) setErrors({ ...errors, savedAmount: null });
              }}
              keyboardType="numeric"
            />
          </View>
          {errors.savedAmount && (
            <Text style={[styles.errorText, { color: theme.error }]}>
              {errors.savedAmount}
            </Text>
          )}
        </View>

        {/* Deadline */}
        <View style={styles.formSection}>
          <Text style={[styles.label, { color: theme.text }]}>
            Deadline (Optional)
          </Text>

          <TouchableOpacity
            style={[
              styles.inputWrapper,
              { backgroundColor: theme.input, borderColor: theme.inputBorder },
            ]}
            onPress={() => setShowDatePicker(true)}
          >
            <Ionicons
              name="calendar-outline"
              size={20}
              color={theme.textSecondary}
              style={styles.inputIcon}
            />
            <Text
              style={[
                styles.dateText,
                { color: deadline ? theme.text : theme.textSecondary },
              ]}
            >
              {deadline ? formatDate(deadline) : "Select a date"}
            </Text>
            {deadline && (
              <TouchableOpacity 
                onPress={() => setDeadline(null)}
                style={styles.clearButton}
              >
                <Ionicons name="close-circle" size={20} color={theme.textSecondary} />
              </TouchableOpacity>
            )}
            <Ionicons
              name="chevron-forward"
              size={20}
              color={theme.textSecondary}
            />
          </TouchableOpacity>

          {showDatePicker && (
            <DateTimePicker
              value={deadline || new Date()}
              mode="date"
              display={Platform.OS === "ios" ? "spinner" : "default"}
              onChange={handleDateChange}
              minimumDate={new Date()}
            />
          )}
        </View>

        {/* Description */}
        <View style={styles.formSection}>
          <Text style={[styles.label, { color: theme.text }]}>
            Description (Optional)
          </Text>
          <View
            style={[
              styles.inputWrapper,
              styles.textAreaWrapper,
              { backgroundColor: theme.input, borderColor: theme.inputBorder },
            ]}
          >
            <TextInput
              style={[styles.input, styles.textArea, { color: theme.text }]}
              placeholder="Add notes about this goal..."
              placeholderTextColor={theme.textSecondary}
              multiline
              numberOfLines={4}
              textAlignVertical="top"
              value={description}
              onChangeText={setDescription}
            />
          </View>
        </View>

        {/* Category Grid */}
        <View style={styles.formSection}>
          <Text style={[styles.label, { color: theme.text }]}>Category *</Text>
          {errors.category && (
            <Text style={[styles.errorText, { color: theme.error, marginBottom: 8 }]}>
              {errors.category}
            </Text>
          )}
          <View style={styles.categoriesGrid}>
            {categories.map((category) => (
              <TouchableOpacity
                key={category.id}
                style={[
                  styles.categoryCard,
                  {
                    backgroundColor: theme.card,
                    borderColor:
                      selectedCategory === category.id
                        ? category.color
                        : errors.category ? theme.error : theme.border,
                    borderWidth: selectedCategory === category.id ? 2 : 1,
                  },
                ]}
                onPress={() => {
                  setSelectedCategory(category.id);
                  if (errors.category) setErrors({ ...errors, category: null });
                }}
              >
                <View
                  style={[
                    styles.categoryIcon,
                    {
                      backgroundColor:
                        selectedCategory === category.id
                          ? `${category.color}20`
                          : isDark
                          ? "#2a2a2a"
                          : "#F8F9FA",
                    },
                  ]}
                >
                  <Ionicons
                    name={category.icon}
                    size={24}
                    color={
                      selectedCategory === category.id
                        ? category.color
                        : theme.textSecondary
                    }
                  />
                </View>
                <Text
                  style={[
                    styles.categoryLabel,
                    {
                      color:
                        selectedCategory === category.id
                          ? theme.text
                          : theme.textSecondary,
                      fontWeight:
                        selectedCategory === category.id ? "600" : "500",
                    },
                  ]}
                >
                  {category.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Save Button */}
        <TouchableOpacity
          style={[
            styles.saveButton, 
            { backgroundColor: submitting ? theme.textSecondary : theme.primary }
          ]}
          onPress={handleSave}
          disabled={submitting}
        >
          {submitting ? (
            <ActivityIndicator size="small" color="#FFFFFF" />
          ) : (
            <Text style={styles.saveButtonText}>Save Goal</Text>
          )}
        </TouchableOpacity>

        <View style={{ height: 40 }} />
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

/* ------------ STYLES (same as Claude) ------------ */
const styles = StyleSheet.create({
  container: { flex: 1 },
  header: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 20,
  },
  backButton: {
    width: 40,
    height: 40,
    alignItems: "center",
    justifyContent: "center",
  },
  headerCenter: { flex: 1, marginLeft: 8 },
  headerTitle: { fontSize: 24, fontWeight: "700" },
  headerSubtitle: { fontSize: 13, marginTop: 2 },
  scrollView: { flex: 1 },
  scrollContent: { paddingHorizontal: 20 },
  formSection: { marginBottom: 24 },
  label: { fontSize: 15, fontWeight: "600", marginBottom: 10 },
  inputWrapper: {
    flexDirection: "row",
    alignItems: "center",
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 16,
    height: 56,
  },
  inputIcon: { marginRight: 12 },
  currencySymbol: { fontSize: 16, marginRight: 4 },
  input: { flex: 1, fontSize: 16 },
  textAreaWrapper: {
    height: 120,
    alignItems: "flex-start",
    paddingVertical: 16,
  },
  textArea: { height: 88 },
  dateText: { flex: 1, fontSize: 16 },
  clearButton: {
    padding: 4,
    marginRight: 4,
  },
  errorText: {
    fontSize: 12,
    marginTop: 4,
  },
  categoriesGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    marginHorizontal: -6,
  },
  categoryCard: {
    width: "22%",
    aspectRatio: 0.9,
    margin: 4,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  categoryIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 6,
  },
  categoryLabel: { fontSize: 10, textAlign: "center" },
  saveButton: {
    height: 56,
    borderRadius: 12,
    justifyContent: "center",
    alignItems: "center",
  },
  saveButtonText: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "600",
  },
});

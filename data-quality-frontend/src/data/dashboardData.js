export const sampleMetrics = [
  { label: "Total batches", value: "128", change: "+12 this week", icon: "layers" },
  { label: "Published batches", value: "96", change: "75% of total", icon: "check" },
  { label: "Blocked batches", value: "18", change: "Requires attention", icon: "shield" },
  { label: "Open exceptions", value: "34", change: "Across all runs", icon: "alert" }
];

export const sampleTrend = [
  { day: "Mon", score: 96.2 }, { day: "Tue", score: 97.1 },
  { day: "Wed", score: 95.8 }, { day: "Thu", score: 98.1 },
  { day: "Fri", score: 97.4 }, { day: "Sat", score: 98.6 },
  { day: "Sun", score: 98.2 }
];

export const sampleStatuses = [
  { name: "PASS", value: 96, color: "#16A34A" },
  { name: "WARN", value: 14, color: "#F59E0B" },
  { name: "BLOCK", value: 18, color: "#DC2626" }
];

export const sampleBatches = [
  { batchId: "BATCH-20261111-001", fileName: "transactions_nov_11.csv", recordCount: 500, overallScore: 99.77, finalStatus: "BLOCK", receivedAt: "2026-11-11 10:15" },
  { batchId: "BATCH-20261110-003", fileName: "daily_settlement.csv", recordCount: 420, overallScore: 97.53, finalStatus: "WARN", receivedAt: "2026-11-10 16:40" },
  { batchId: "BATCH-20261110-002", fileName: "corrected_transactions.csv", recordCount: 500, overallScore: 100, finalStatus: "PASS", receivedAt: "2026-11-10 14:20" },
  { batchId: "BATCH-20261109-004", fileName: "card_payments.csv", recordCount: 315, overallScore: 98.12, finalStatus: "PASS", receivedAt: "2026-11-09 11:05" }
];

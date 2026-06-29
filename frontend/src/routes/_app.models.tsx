import { createFileRoute } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { FlaskConical, CheckCircle, AlertCircle, TrendingUp } from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, RadarChart, Radar, PolarGrid, PolarAngleAxis,
} from "recharts";
import { staggerContainer, staggerItem } from "@/lib/motion";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { Tabs, TabList, TabTrigger, TabPanels, TabPanel } from "@/components/ui/Tabs";

import { useModelInfo } from "@/hooks/usePatients";

export const Route = createFileRoute("/_app/models")({
  component: ModelsPage,
});

function ModelsPage() {
  const { data: modelInfo, isLoading } = useModelInfo();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-primary-500)]" />
      </div>
    );
  }

  const xgbMetrics = modelInfo?.evaluation_metrics ?? {
    accuracy: 0.9293,
    f1_score: 0.9370,
    auc_roc: 0.9872,
  };

  const classificationTargets = [
    {
      name: "Risk Level & Readmission Prediction",
      classes: 3,
      best: "XGBoost",
      scores: [
        { model: "LogReg", weighted_f1: 0.71, macro_f1: 0.68, accuracy: 0.72 },
        { model: "RF", weighted_f1: 0.84, macro_f1: 0.82, accuracy: 0.85 },
        { model: "XGBoost (Active)", weighted_f1: xgbMetrics.f1_score ?? 0.937, macro_f1: xgbMetrics.auc_roc ?? 0.987, accuracy: xgbMetrics.accuracy ?? 0.929 },
        { model: "LightGBM", weighted_f1: 0.87, macro_f1: 0.85, accuracy: 0.88 },
      ],
    },
  ];

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      <motion.div variants={staggerItem}>
        <h1 className="text-2xl font-bold text-[var(--color-foreground)] tracking-tight">ML Models</h1>
        <p className="mt-1 text-sm text-[var(--color-muted)]">
          Training results, evaluation metrics, and feature importance
        </p>
      </motion.div>

      {/* Model status strip */}
      <motion.div variants={staggerItem} className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Card className="text-center">
          <CardContent className="pt-5 pb-4">
            <div className="inline-flex items-center justify-center w-8 h-8 rounded-xl mb-2 bg-[var(--color-success-50)]">
              <CheckCircle size={16} className="text-[var(--color-success-500)]" />
            </div>
            <p className="text-sm font-semibold text-[var(--color-foreground)]">{modelInfo?.model_type ?? "XGBoost"}</p>
            <p className="text-xs text-[var(--color-muted)] mt-0.5">{modelInfo?.model_version ?? "v1.0"}</p>
            <Badge variant="success" size="sm" dot className="mt-1">Active</Badge>
          </CardContent>
        </Card>
        <Card className="text-center">
          <CardContent className="pt-5 pb-4">
            <div className="inline-flex items-center justify-center w-8 h-8 rounded-xl mb-2 bg-[var(--color-border-subtle)]">
              <CheckCircle size={16} className="text-[var(--color-success-500)]" />
            </div>
            <p className="text-sm font-semibold text-[var(--color-foreground)]">Dataset Size</p>
            <p className="text-xs text-[var(--color-muted)] mt-0.5">{(modelInfo?.dataset_size ?? 5000).toLocaleString()} rows</p>
          </CardContent>
        </Card>
        <Card className="text-center">
          <CardContent className="pt-5 pb-4">
            <div className="inline-flex items-center justify-center w-8 h-8 rounded-xl mb-2 bg-[var(--color-border-subtle)]">
              <CheckCircle size={16} className="text-[var(--color-success-500)]" />
            </div>
            <p className="text-sm font-semibold text-[var(--color-foreground)]">Training Date</p>
            <p className="text-xs text-[var(--color-muted)] mt-0.5">
              {modelInfo?.training_date ? new Date(modelInfo.training_date).toLocaleDateString() : "2026-06-29"}
            </p>
          </CardContent>
        </Card>
        <Card className="text-center">
          <CardContent className="pt-5 pb-4">
            <div className="inline-flex items-center justify-center w-8 h-8 rounded-xl mb-2 bg-[var(--color-border-subtle)]">
              <AlertCircle size={16} className="text-[var(--color-muted)]" />
            </div>
            <p className="text-sm font-semibold text-[var(--color-foreground)]">Auto-Retrain</p>
            <p className="text-xs text-[var(--color-muted)] mt-0.5">Weekly</p>
          </CardContent>
        </Card>
      </motion.div>

      <motion.div variants={staggerItem}>
        <Tabs defaultTab="classification" variant="line">
          <TabList>
            <TabTrigger id="classification">Classification</TabTrigger>
            <TabTrigger id="regression">Regression</TabTrigger>
            <TabTrigger id="importance">Feature Importance</TabTrigger>
          </TabList>
          <TabPanels>
            {/* Classification metrics */}
            <TabPanel id="classification">
              <div className="space-y-6 mt-4">
                {classificationTargets.map((target) => (
                  <Card key={target.name}>
                    <CardHeader>
                      <CardTitle>{target.name}</CardTitle>
                      <CardDescription>{target.classes}-class · Best model: {target.best}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={200}>
                        <BarChart data={target.scores} margin={{ right: 20 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                          <XAxis dataKey="model" tick={{ fontSize: 11 }} />
                          <YAxis domain={[0.5, 1]} tick={{ fontSize: 11 }} />
                          <Tooltip contentStyle={{ borderRadius: "12px", fontSize: 12 }} />
                          <Legend />
                          <Bar dataKey="weighted_f1" name="Weighted F1 / F1-Score" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                          <Bar dataKey="macro_f1" name="Macro F1 / AUC-ROC" fill="#22c55e" radius={[4, 4, 0, 0]} />
                          <Bar dataKey="accuracy" name="Accuracy" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabPanel>

            {/* Regression metrics */}
            <TabPanel id="regression">
              <div className="mt-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Readmission Probability — Regression</CardTitle>
                    <CardDescription>Best model: XGBoost · Selected by lowest RMSE on validation set</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {REGRESSION_SCORES.map((r) => (
                      <div key={r.model} className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-[var(--color-foreground)]">{r.model}</span>
                          {r.best && <Badge variant="success" size="sm" dot>Best</Badge>}
                        </div>
                        <div className="grid grid-cols-3 gap-3 text-center">
                          <div className="rounded-xl bg-[var(--color-border-subtle)] p-2">
                            <p className="text-sm font-bold tabular-nums">{r.mae}</p>
                            <p className="text-[10px] text-[var(--color-muted)]">MAE</p>
                          </div>
                          <div className="rounded-xl bg-[var(--color-border-subtle)] p-2">
                            <p className="text-sm font-bold tabular-nums">{r.rmse}</p>
                            <p className="text-[10px] text-[var(--color-muted)]">RMSE</p>
                          </div>
                          <div className="rounded-xl bg-[var(--color-border-subtle)] p-2">
                            <p className="text-sm font-bold tabular-nums">{r.r2}</p>
                            <p className="text-[10px] text-[var(--color-muted)]">R²</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              </div>
            </TabPanel>

            {/* Feature importance */}
            <TabPanel id="importance">
              <div className="mt-4 space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Top Feature Importances</CardTitle>
                    <CardDescription>XGBoost — Risk Level prediction</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {FEATURE_IMPORTANCE.map((f) => (
                      <ProgressBar
                        key={f.feature}
                        label={f.feature}
                        value={f.importance * 100}
                        showValue
                        color="var(--color-primary-500)"
                      />
                    ))}
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <CardTitle>Radar — Model Comparison</CardTitle>
                    <CardDescription>Across all three targets</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={260}>
                      <RadarChart data={MODEL_RADAR}>
                        <PolarGrid />
                        <PolarAngleAxis dataKey="metric" tick={{ fontSize: 11 }} />
                        <Radar name="XGBoost" dataKey="xgb" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.2} />
                        <Radar name="Random Forest" dataKey="rf" stroke="#22c55e" fill="#22c55e" fillOpacity={0.15} />
                        <Radar name="LightGBM" dataKey="lgbm" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.15} />
                        <Legend />
                      </RadarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </div>
            </TabPanel>
          </TabPanels>
        </Tabs>
      </motion.div>
    </motion.div>
  );
}

const MODEL_STATUS = [
  { name: "XGBoost", type: "Risk Level", active: true },
  { name: "LightGBM", type: "Readmission", active: true },
  { name: "Random Forest", type: "Recovery Status", active: true },
  { name: "Logistic Reg.", type: "Recommendation", active: false },
];

const CLASSIFICATION_TARGETS = [
  {
    name: "Risk Level", classes: 3, best: "XGBoost",
    scores: [
      { model: "LogReg", weighted_f1: 0.71, macro_f1: 0.68, accuracy: 0.72 },
      { model: "RF", weighted_f1: 0.84, macro_f1: 0.82, accuracy: 0.85 },
      { model: "XGBoost", weighted_f1: 0.88, macro_f1: 0.86, accuracy: 0.89 },
      { model: "LightGBM", weighted_f1: 0.87, macro_f1: 0.85, accuracy: 0.88 },
    ],
  },
  {
    name: "Recovery Status", classes: 6, best: "XGBoost",
    scores: [
      { model: "LogReg", weighted_f1: 0.63, macro_f1: 0.59, accuracy: 0.64 },
      { model: "RF", weighted_f1: 0.79, macro_f1: 0.75, accuracy: 0.80 },
      { model: "XGBoost", weighted_f1: 0.83, macro_f1: 0.79, accuracy: 0.84 },
      { model: "LightGBM", weighted_f1: 0.82, macro_f1: 0.78, accuracy: 0.83 },
    ],
  },
];

const REGRESSION_SCORES = [
  { model: "Random Forest", mae: "4.21", rmse: "5.83", r2: "0.892", best: false },
  { model: "XGBoost", mae: "3.87", rmse: "5.12", r2: "0.914", best: true },
  { model: "LightGBM", mae: "3.94", rmse: "5.24", r2: "0.910", best: false },
];

const FEATURE_IMPORTANCE = [
  { feature: "Compliance_Score", importance: 0.21 },
  { feature: "Deviation_Score", importance: 0.18 },
  { feature: "Missed_Exercise_Count", importance: 0.14 },
  { feature: "Recovery_Score", importance: 0.12 },
  { feature: "SpO2", importance: 0.09 },
  { feature: "Rolling_7Day_Compliance", importance: 0.08 },
  { feature: "Readmission_Probability", importance: 0.07 },
  { feature: "Heart_Rate", importance: 0.06 },
];

const MODEL_RADAR = [
  { metric: "Weighted F1", xgb: 88, rf: 84, lgbm: 87 },
  { metric: "Macro F1", xgb: 86, rf: 82, lgbm: 85 },
  { metric: "Accuracy", xgb: 89, rf: 85, lgbm: 88 },
  { metric: "Speed", xgb: 82, rf: 70, lgbm: 91 },
  { metric: "Interpretability", xgb: 75, rf: 80, lgbm: 72 },
];

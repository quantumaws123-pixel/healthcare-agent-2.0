import { useQuery } from "@tanstack/react-query";
import { getPatients, getDashboardStats, getPatientSummary, getLatestPatientRecord, getModelInfo, queryKeys, type GetPatientsParams } from "@/lib/api";

export function usePatients(params: GetPatientsParams = {}) {
  return useQuery({
    queryKey: queryKeys.patients(params),
    queryFn: () => getPatients(params),
  });
}

export function usePatientSummary(patientId: string) {
  return useQuery({
    queryKey: queryKeys.patientSummary(patientId),
    queryFn: () => getPatientSummary(patientId),
    enabled: Boolean(patientId),
  });
}

export function usePatientLatest(patientId: string) {
  return useQuery({
    queryKey: queryKeys.patientLatest(patientId),
    queryFn: () => getLatestPatientRecord(patientId),
    enabled: Boolean(patientId),
  });
}

export function useDashboardStats() {
  return useQuery({
    queryKey: queryKeys.dashboardStats(),
    queryFn: getDashboardStats,
  });
}

export function useModelInfo() {
  return useQuery({
    queryKey: queryKeys.modelInfo(),
    queryFn: getModelInfo,
  });
}

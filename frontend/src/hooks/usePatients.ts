import { useQuery } from "@tanstack/react-query";
import {
  getPatients,
  getDashboardStats,
  getPatientSummary,
  getLatestPatientRecord,
  getModelInfo,
  getMyDoctorPatients,
  getTodayVitals,
  getVitalsHistory,
  getCarePlan,
  getMyPatientProfile,
  getAssignedDoctor,
  getMedicalHistory,
  queryKeys,
  hospitalQueryKeys,
  type GetPatientsParams,
} from "@/lib/api";

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
    retry: 1,
  });
}

export function useDashboardStats() {
  return useQuery({
    queryKey: queryKeys.dashboardStats(),
    queryFn: getDashboardStats,
    staleTime: 5 * 60 * 1000,
  });
}

export function useModelInfo() {
  return useQuery({
    queryKey: queryKeys.modelInfo(),
    queryFn: getModelInfo,
    staleTime: 10 * 60 * 1000,
    retry: 1,
  });
}

export function useMyDoctorPatients() {
  return useQuery({
    queryKey: hospitalQueryKeys.myDoctorPatients(),
    queryFn: getMyDoctorPatients,
  });
}

export function useTodayVitals() {
  return useQuery({
    queryKey: hospitalQueryKeys.todayVitals(),
    queryFn: getTodayVitals,
    staleTime: 5 * 60 * 1000,
  });
}

export function useCarePlan(patientUserId: string) {
  return useQuery({
    queryKey: hospitalQueryKeys.carePlan(patientUserId),
    queryFn: () => getCarePlan(patientUserId),
    enabled: Boolean(patientUserId),
  });
}

export function useMyPatientProfile() {
  return useQuery({
    queryKey: hospitalQueryKeys.myProfile(),
    queryFn: getMyPatientProfile,
    retry: 1,
    staleTime: 5 * 60 * 1000,
  });
}

export function useAssignedDoctor(patientUserId: string) {
  return useQuery({
    queryKey: hospitalQueryKeys.assignedDoctor(patientUserId),
    queryFn: () => getAssignedDoctor(patientUserId),
    enabled: Boolean(patientUserId),
  });
}

export function useMedicalHistory(patientUserId: string) {
  return useQuery({
    queryKey: hospitalQueryKeys.medicalHistory(patientUserId),
    queryFn: () => getMedicalHistory(patientUserId),
    enabled: Boolean(patientUserId),
  });
}

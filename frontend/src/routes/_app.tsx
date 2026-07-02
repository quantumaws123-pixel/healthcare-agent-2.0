import { createFileRoute, Outlet, redirect } from "@tanstack/react-router";
import { AppShell } from "@/components/layout/AppShell";
import { getAccessToken, getStoredUser } from "@/lib/auth";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getMyPatientProfile, hospitalQueryKeys } from "@/lib/api";
import { OnboardingWizard } from "@/components/patient/OnboardingWizard";

export const Route = createFileRoute("/_app")({
  beforeLoad: () => {
    if (!getAccessToken() || !getStoredUser()) {
      throw redirect({ to: "/login" });
    }
  },
  component: AppLayout,
});

function AppLayout() {
  const user = getStoredUser();
  const queryClient = useQueryClient();
  const isPatient = user?.role === "patient";

  // Only fetch profile for patients — doctors/admins skip this entirely
  const { data: profile, isLoading } = useQuery({
    queryKey: hospitalQueryKeys.myProfile(),
    queryFn: getMyPatientProfile,
    enabled: isPatient,
    retry: 1,
    staleTime: 5 * 60 * 1000,
  });

  // While loading profile for patient, show a brief spinner instead of the app
  if (isPatient && isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-950">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500" />
      </div>
    );
  }

  // Show onboarding wizard only for patients who haven't completed it
  if (isPatient && !isLoading && (!profile || !profile.onboarding_completed)) {
    return (
      <OnboardingWizard
        onComplete={() => {
          queryClient.invalidateQueries({ queryKey: hospitalQueryKeys.myProfile() });
          queryClient.invalidateQueries({ queryKey: ["patient-latest", user?.id ?? ""] });
        }}
      />
    );
  }

  // Doctors, admins, and onboarded patients go straight to the app
  return (
    <AppShell>
      <Outlet />
    </AppShell>
  );
}

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

  // For patients, check if onboarding is complete
  const { data: profile, isLoading, isError } = useQuery({
    queryKey: hospitalQueryKeys.myProfile(),
    queryFn: getMyPatientProfile,
    enabled: user?.role === "patient",
    retry: 1,
    staleTime: 5 * 60 * 1000,
  });

  // Show onboarding wizard for patients who haven't completed it (or if profile missing)
  if (user?.role === "patient" && !isLoading) {
    const needsOnboarding = isError || !profile || !profile.onboarding_completed;
    if (needsOnboarding) {
      return (
        <OnboardingWizard
          onComplete={() => {
            queryClient.invalidateQueries({ queryKey: hospitalQueryKeys.myProfile() });
            queryClient.invalidateQueries({ queryKey: ["patient-latest", user.id] });
          }}
        />
      );
    }
  }

  return (
    <AppShell>
      <Outlet />
    </AppShell>
  );
}

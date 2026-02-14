import { create } from "zustand";
import { persist } from "zustand/middleware";
import { apiClient } from "../api/client";

export interface Organization {
    id: string;
    name: string;
    slug: string;
    created_at: string;
}

interface OrgState {
    currentOrgId: string | null;
    orgs: Organization[];
    currentOrg: Organization | null;
    setOrgs: (orgs: Organization[]) => void;
    setCurrentOrg: (orgId: string) => void;
    fetchOrgs: () => Promise<Organization[]>;
    clearOrgs: () => void;
}

export const useOrgStore = create<OrgState>()(
    persist(
        (set, get) => ({
            currentOrgId: null,
            orgs: [],
            currentOrg: null,
            setOrgs: (orgs) => set({ orgs }),
            setCurrentOrg: (orgId) => {
                const org = get().orgs.find((o) => o.id === orgId) || null;
                set({ currentOrgId: orgId, currentOrg: org });
            },
            fetchOrgs: async () => {
                try {
                    const response = await apiClient.get("/organizations/me");
                    const orgs: Organization[] = response.data;
                    set({ orgs });

                    // Auto-select first org if none selected
                    const currentId = get().currentOrgId;
                    if (orgs.length > 0 && (!currentId || !orgs.find((o) => o.id === currentId))) {
                        set({
                            currentOrgId: orgs[0].id,
                            currentOrg: orgs[0]
                        });
                    }
                    return orgs;
                } catch (error) {
                    console.error("Failed to fetch organizations", error);
                    return [];
                }
            },
            clearOrgs: () => set({ currentOrgId: null, orgs: [], currentOrg: null }),
        }),
        {
            name: "org-storage",
        }
    )
);

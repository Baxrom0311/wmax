import { create } from "zustand";
import type { AlertLevel } from "../lib/types";

interface FilterState {
  district: string | null;
  level: AlertLevel | null;
  searchQuery: string;

  setDistrict: (district: string | null) => void;
  setLevel: (level: AlertLevel | null) => void;
  setSearchQuery: (query: string) => void;
  resetFilters: () => void;
}

export const useFilterStore = create<FilterState>((set) => ({
  district: null,
  level: null,
  searchQuery: "",

  setDistrict: (district) => set({ district }),
  setLevel: (level) => set({ level }),
  setSearchQuery: (searchQuery) => set({ searchQuery }),
  resetFilters: () => set({ district: null, level: null, searchQuery: "" }),
}));

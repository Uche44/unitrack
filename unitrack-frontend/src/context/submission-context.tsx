import { create } from "zustand";

type Milestone = "proposal" | "chapter_one" | "chapter_two" | "final_report";

interface SubmissionState {
  projectId: number | null;
  currentStage: Milestone;

  setProjectId: (id: number) => void;
  setCurrentStage: (stage: Milestone) => void;
  advanceStage: () => void;
  buttonLabel: () => string;
  loading: boolean;
  setLoading: (loading: boolean) => void;
}

export const useSubmissionStore = create<SubmissionState>((set, get) => ({
  projectId: null,
  currentStage: "proposal",
  loading: false,
  setLoading: (loading: boolean) => set({ loading }),
  setProjectId: (id) => set({ projectId: id }),

  setCurrentStage: (stage) => set({ currentStage: stage }),

  advanceStage: () => {
    const order: Milestone[] = [
      "proposal",
      "chapter_one",
      "chapter_two",
      "final_report",
    ];

    const index = order.indexOf(get().currentStage);
    if (index < order.length - 1) {
      set({ currentStage: order[index + 1] });
    }
  },

  buttonLabel: () => {
    const stage = get().currentStage;
    if (stage === "proposal") return "Create Project";
    return `Submit ${stage.replace("_", " ")}`;
  },
}));

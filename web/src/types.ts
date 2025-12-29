export interface DebaterStats {
  name: string;
  side_win_rates: {
    total: number;
    aff: number;
    neg: number;
  };
  positions_speaker_points: {
    "1": number;
    "2": number;
    "3": number;
  };
  motion_category_stats: {
    top_3: CategoryStat[];
    bottom_3: CategoryStat[];
  };
  debates: Debate[];
}

export interface CategoryStat {
  category: string;
  win_rate: number;
}

export interface Debate {
  ballots_gained: number;
  opponent: string;
  was_aff: boolean;
  link: string;
  speaker_points: number;
  date: string;
}

export interface AppState {
  allDebaters: DebaterStats[];
  currentDebater: DebaterStats | null;
}
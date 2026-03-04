export interface Patient {
  age: number;
  sex: "male" | "female";
  name?: string;
}

export interface ReferenceRange {
  low: number | null;
  high: number | null;
}

export interface TrendResult {
  direction: "up" | "down" | "stable";
  delta: number;
  percent_change: number;
  rate_per_day: number;
  projected_days_to_critical: number | null;
}

export interface InterpretationResult {
  status: "normal" | "low" | "high" | "critical_low" | "critical_high" | "unknown";
  value: number;
  unit: string;
  reference_range: ReferenceRange | null;
  plain_text: string;
  severity_score: number;
  flag_color: "green" | "amber" | "red" | "gray";
  trend?: TrendResult;
  previous_value?: number;
}

export interface MatchedPattern {
  id: string;
  name: string;
  category: string;
  severity: "low" | "moderate" | "high" | "critical";
  interpretation: string;
  harrison_ref: string;
  confidence: number;
  matched_criteria: string;
}

export interface StagingResult {
  stage: string;
  label: string;
  color?: string;
  description: string;
  show?: boolean;
}

export interface FurtherTest {
  test_name: string;
  rationale: string;
}

export interface FurtherTestGroup {
  pattern_id: string;
  tests: FurtherTest[];
}

export interface ReferralResult {
  pattern_id: string;
  specialist: string;
  urgency: "routine" | "soon" | "urgent";
  reason: string;
  when_to_refer?: string;
}

export interface LifestylePlan {
  diet: string[];
  exercise: Array<{
    type: string;
    duration: string;
    frequency: string;
    precautions?: string;
  }>;
  sleep: string[];
  stress: string[];
  weight?: string[] | null;
  smoking?: string[] | null;
}

export interface Tier2Result {
  patterns: MatchedPattern[];
  staging: Record<string, StagingResult>;
}

export interface Tier3Result {
  further_tests: FurtherTestGroup[];
  referrals: ReferralResult[];
  lifestyle: LifestylePlan;
}

export interface RAGNarrative {
  narrative: string;
  differentials: string[];
  confidence: number;
  harrison_citations: string[];
  caveats: string[];
}

export interface AnalysisResult {
  id: string;
  timestamp: string;
  patient: Patient;
  tier1: Record<string, InterpretationResult>;
  tier2: Tier2Result;
  tier3: Tier3Result;
  rag_narrative?: RAGNarrative;
}

export interface UploadResponse {
  patient: Record<string, string | null>;
  parsed_results: Record<string, number>;
  results_detail?: Record<string, {
    value: number | string;
    unit: string;
    ref_range: string;
    source_page: number;
  }>;
  urine?: Record<string, {
    value: string;
    ref_range: string;
    abnormal: boolean;
  }>;
  tumor_markers?: Record<string, {
    value: number | string;
    unit: string;
    ref_range: string;
  }>;
  confidence: number;
  total_tests_found: number;
  unmatched: string[];
}

export interface PanelInfo {
  test_id: string;
  name: string;
  unit: string;
}

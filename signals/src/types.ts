export type Role = "owner" | "friend";
export type Vote = "more" | "less";
export type RequestStatus = "pending" | "approved" | "rejected";

export interface Reader {
  device: string;
  email: string;
  role: Role;
}

// Feedback belongs to the reader, not the device, so every enrolled device
// shows the same state.
export interface Feedback {
  story: string;
  vote: Vote | null;
  knew: boolean;
  follow: boolean;
  note: string;
}

export interface StoryRequest {
  id: string;
  url: string;
  note: string;
  status: RequestStatus;
  from: string;
  createdAt: number;
}

export interface StoryTally {
  story: string;
  more: number;
  less: number;
  knew: number;
  follow: number;
  notes: string[];
}

// What the digest runs read: approved requests no run has used yet, and the
// feedback updated in the window, totaled per story. Only the owner can write
// notes, so every note is the owner's.
export interface Signals {
  requests: Pick<StoryRequest, "id" | "url" | "note">[];
  feedback: StoryTally[];
}

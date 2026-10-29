import type { Feedback, StoryTally, Vote } from "../types";

type FeedbackRow = {
  story: string;
  vote: Vote | null;
  knew: number;
  follow: number;
  note: string;
};

type TallyRow = Omit<StoryTally, "notes"> & { notes: string };

export class FeedbackStore {
  readonly #sql: SqlStorage;

  constructor(sql: SqlStorage) {
    this.#sql = sql;
  }

  forDay(email: string, day: string): Feedback[] {
    return this.#sql
      .exec<FeedbackRow>(
        `SELECT story, vote, knew, follow, note FROM feedback
         WHERE email = ? AND story LIKE ? ORDER BY story`,
        email,
        `${day}/%`,
      )
      .toArray()
      .map((row) => ({
        ...row,
        knew: row.knew === 1,
        follow: row.follow === 1,
      }));
  }

  // Clearing every field deletes the row, so the table holds only feedback
  // a reader actually gave.
  save(email: string, { story, vote, knew, follow, note }: Feedback): void {
    if (vote === null && !knew && !follow && note === "") {
      this.#sql.exec(
        "DELETE FROM feedback WHERE email = ? AND story = ?",
        email,
        story,
      );
      return;
    }

    this.#sql.exec(
      `INSERT INTO feedback (email, story, vote, knew, follow, note, updated_at)
       VALUES (?, ?, ?, ?, ?, ?, ?)
       ON CONFLICT DO UPDATE SET vote = excluded.vote, knew = excluded.knew,
         follow = excluded.follow, note = excluded.note,
         updated_at = excluded.updated_at`,
      email,
      story,
      vote,
      Number(knew),
      Number(follow),
      note,
      Date.now(),
    );
  }

  tally(since: number): StoryTally[] {
    return this.#sql
      .exec<TallyRow>(
        `SELECT story,
           SUM(vote = 'more') AS more, SUM(vote = 'less') AS less,
           SUM(knew) AS knew, SUM(follow) AS follow,
           json_group_array(note) FILTER (WHERE note != '') AS notes
         FROM feedback WHERE updated_at >= ?
         GROUP BY story ORDER BY story`,
        since,
      )
      .toArray()
      .map((row) => ({ ...row, notes: JSON.parse(row.notes) as string[] }));
  }
}

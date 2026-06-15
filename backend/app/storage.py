import json
import sqlite3
from pathlib import Path

from backend.app.models import EpisodeResult


class EpisodeStore:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def save_episode(self, episode: EpisodeResult) -> None:
        payload = episode.model_dump(mode="json")
        with self._connect() as connection:
            connection.execute("delete from scores where episode_id = ?", (episode.id,))
            connection.execute(
                """
                insert or replace into episodes
                    (id, title, challenge_type, winner, created_at, payload)
                values (?, ?, ?, ?, ?, ?)
                """,
                (
                    episode.id,
                    episode.title,
                    episode.challenge_type.value,
                    episode.winner,
                    episode.created_at.isoformat(),
                    json.dumps(payload, indent=2),
                ),
            )
            for result in episode.contestants:
                if result.score is None:
                    continue
                connection.execute(
                    """
                    insert into scores
                        (episode_id, contestant, provider, model, total, correctness,
                         creativity, clarity, resilience, usefulness, rationale)
                    values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        episode.id,
                        result.contestant.label,
                        result.contestant.provider,
                        result.contestant.model,
                        result.score.total,
                        result.score.correctness,
                        result.score.creativity,
                        result.score.clarity,
                        result.score.resilience,
                        result.score.usefulness,
                        result.score.rationale,
                    ),
                )

    def list_episodes(self, limit: int = 20) -> list[dict[str, object]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                select id, title, challenge_type, winner, created_at
                from episodes
                order by created_at desc
                limit ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_episode(self, episode_id: str) -> EpisodeResult | None:
        with self._connect() as connection:
            row = connection.execute(
                "select payload from episodes where id = ?",
                (episode_id,),
            ).fetchone()
        if row is None:
            return None
        return EpisodeResult.model_validate_json(row["payload"])

    def get_q_value(self, state: str, action: str) -> float:
        with self._connect() as connection:
            row = connection.execute(
                "select q_value from q_values where state = ? and action = ?",
                (state, action),
            ).fetchone()
        if row is None:
            return 0
        return float(row["q_value"])

    def get_best_q_value(self, state: str) -> float:
        with self._connect() as connection:
            row = connection.execute(
                "select max(q_value) as best_q from q_values where state = ?",
                (state,),
            ).fetchone()
        if row is None or row["best_q"] is None:
            return 0
        return float(row["best_q"])

    def get_action_updates(self, state: str, action: str) -> int:
        with self._connect() as connection:
            row = connection.execute(
                "select updates from q_values where state = ? and action = ?",
                (state, action),
            ).fetchone()
        if row is None:
            return 0
        return int(row["updates"])

    def get_total_q_updates(self, state: str) -> int:
        with self._connect() as connection:
            row = connection.execute(
                "select sum(updates) as total_updates from q_values where state = ?",
                (state,),
            ).fetchone()
        if row is None or row["total_updates"] is None:
            return 0
        return int(row["total_updates"])

    def set_q_value(self, state: str, action: str, q_value: float) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                insert into q_values (state, action, q_value, updates)
                values (?, ?, ?, 1)
                on conflict(state, action) do update set
                    q_value = excluded.q_value,
                    updates = updates + 1
                """,
                (state, action, q_value),
            )

    def q_table(self, limit: int = 100) -> list[dict[str, object]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                select state, action, round(q_value, 4) as q_value, updates
                from q_values
                order by q_value desc, updates desc
                limit ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def leaderboard(self, limit: int = 20) -> list[dict[str, object]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                select contestant, provider, model,
                       count(*) as episodes,
                       round(avg(total), 2) as avg_score,
                       max(total) as best_score
                from scores
                group by contestant, provider, model
                order by avg_score desc, best_score desc
                limit ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                create table if not exists episodes (
                    id text primary key,
                    title text not null,
                    challenge_type text not null,
                    winner text,
                    created_at text not null,
                    payload text not null
                )
                """
            )
            connection.execute(
                """
                create table if not exists scores (
                    id integer primary key autoincrement,
                    episode_id text not null,
                    contestant text not null,
                    provider text not null,
                    model text not null,
                    total integer not null,
                    correctness integer not null,
                    creativity integer not null,
                    clarity integer not null,
                    resilience integer not null,
                    usefulness integer not null,
                    rationale text not null,
                    foreign key (episode_id) references episodes(id)
                )
                """
            )
            connection.execute(
                """
                create table if not exists q_values (
                    state text not null,
                    action text not null,
                    q_value real not null,
                    updates integer not null default 0,
                    primary key (state, action)
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

import asyncio

import streamlit as st

from backend.app.arena import ArenaRunner
from backend.app.branding import APP_NAME, APP_TAGLINE
from backend.app.config import get_settings
from backend.app.models import ChallengeType, EpisodeRequest, ProviderModel
from backend.app.setup import RECOMMENDED_OLLAMA_MODELS, get_setup_status, pull_recommended_model
from backend.app.storage import EpisodeStore


st.set_page_config(page_title=APP_NAME, page_icon="PX", layout="wide")


def run_async(coro):
    return asyncio.run(coro)


settings = get_settings()
store = EpisodeStore(settings.database_path)

st.title(APP_NAME)
st.caption(APP_TAGLINE)

tabs = st.tabs(["Setup", "Run Episode", "Leaderboard", "Agentic Brain", "Replays"])

with tabs[0]:
    st.subheader("Local Setup")
    status = run_async(get_setup_status(settings))

    if status.ollama_running:
        st.success("Ollama is running.")
    else:
        st.error("Ollama is not reachable. Install/start Ollama, then refresh this page.")
        st.code("ollama serve", language="bash")

    st.write("Provider status")
    st.json(status.provider_status)

    st.write("Recommended free local models")
    for model in status.recommended_models:
        col1, col2, col3 = st.columns([3, 2, 2])
        col1.write(f"**{model.id}**")
        col2.write(model.size or "size unknown")
        if model.installed:
            col3.success("Installed")
        elif status.ollama_running:
            if col3.button(f"Pull {model.id}", key=f"pull-{model.id}"):
                with st.spinner(f"Pulling {model.id}. This can take a while."):
                    messages = run_async(pull_recommended_model(settings, model.id))
                st.success(f"Finished pulling {model.id}.")
                if messages:
                    st.write(messages[-5:])
        else:
            col3.warning("Start Ollama first")

    st.info(
        "No API key is required for Ollama. Hugging Face and NVIDIA providers are optional "
        "bring-your-own-key features configured only in your local .env."
    )

with tabs[1]:
    st.subheader("Create an Episode")
    status = run_async(get_setup_status(settings))
    installed_ollama = [model.id for model in status.installed_models]

    if not installed_ollama:
        st.warning("Install at least one Ollama model from the Setup tab before running an episode.")
    else:
        title = st.text_input("Episode title", value="Chaos Challenge 001")
        challenge_type = st.selectbox(
            "Challenge type",
            options=[item.value for item in ChallengeType],
            index=1,
        )
        challenge = st.text_area(
            "Challenge",
            value=(
                "Design a tiny but secure note-taking app for students. Include the core "
                "features, architecture, risks, and one unique twist."
            ),
            height=150,
        )
        contestants = st.multiselect(
            "Contestant models",
            options=installed_ollama,
            default=installed_ollama[: min(3, len(installed_ollama))],
        )
        use_reinforcement = st.checkbox(
            "Use Q-learning reinforcement memory",
            value=True,
            help="Updates a local Q-table after each episode using score, latency, and error signals.",
        )
        use_goal_engine = st.checkbox(
            "Use goal-based agent engine",
            value=True,
            help="Creates challenge-specific goals and evaluates whether the episode met them.",
        )
        use_utility_engine = st.checkbox(
            "Use utility-based decision engine",
            value=True,
            help="Ranks agents with utility = quality prior + Q-value + exploration - penalties.",
        )
        auto_pick_judge = st.checkbox(
            "Let the agentic engine pick the judge/critic model",
            value=True,
            help="Uses utility-based selection first, then Q-learning/UCB if utility is disabled.",
        )
        judge_model = None
        if not auto_pick_judge:
            judge_model = st.selectbox("Judge/host/critic model", options=installed_ollama)
        temperature = st.slider("Contestant creativity", 0.0, 1.5, 0.7, 0.1)

        if st.button("Start Episode", type="primary"):
            if not contestants:
                st.error("Select at least one contestant model.")
                st.stop()
            request = EpisodeRequest(
                title=title,
                challenge=challenge,
                challenge_type=ChallengeType(challenge_type),
                contestants=[
                    ProviderModel(provider="ollama", model=model) for model in contestants
                ],
                judge_model=(
                    ProviderModel(provider="ollama", model=judge_model)
                    if judge_model
                    else None
                ),
                use_reinforcement=use_reinforcement,
                use_goal_engine=use_goal_engine,
                use_utility_engine=use_utility_engine,
                temperature=temperature,
            )
            with st.spinner("Agents are competing, criticizing, revising, and judging..."):
                episode = run_async(ArenaRunner(settings).run_episode(request))
                store.save_episode(episode)

            st.success(f"Winner: {episode.winner or 'No winner'}")
            st.markdown("### Host Intro")
            st.write(episode.host_intro)
            st.markdown("### Final Recap")
            st.write(episode.final_summary)
            if episode.learning_signals:
                st.markdown("### Q-Learning Updates")
                st.dataframe(
                    [signal.model_dump() for signal in episode.learning_signals],
                    use_container_width=True,
                )
            if episode.goals:
                st.markdown("### Goal-Based Agent Trace")
                st.dataframe(
                    [goal.model_dump() for goal in episode.goals],
                    use_container_width=True,
                )
            if episode.decisions:
                st.markdown("### Utility/Policy Decisions")
                for decision in episode.decisions:
                    with st.expander(f"{decision.phase}: {decision.algorithm} -> {decision.selected_action}"):
                        st.write(decision.reason)
                        st.code(f"state = {decision.state}", language="text")
                        if decision.candidates:
                            st.dataframe(
                                [candidate.model_dump() for candidate in decision.candidates],
                                use_container_width=True,
                            )

            for result in episode.contestants:
                score = result.score.total if result.score else 0
                with st.expander(f"{result.contestant.label} - Score {score}/50"):
                    st.markdown("#### First Answer")
                    st.write(result.first_answer.content or result.first_answer.error)
                    st.markdown("#### Critique")
                    st.write(result.critique.content or result.critique.error)
                    st.markdown("#### Revised Answer")
                    st.write(result.revised_answer.content or result.revised_answer.error)
                    if result.score:
                        st.markdown("#### Scorecard")
                        st.json(result.score.model_dump())

with tabs[2]:
    st.subheader("Season Leaderboard")
    leaderboard = store.leaderboard()
    if leaderboard:
        st.dataframe(leaderboard, use_container_width=True)
    else:
        st.info("No episodes scored yet.")

with tabs[3]:
    st.subheader("Agentic Brain")
    st.markdown("#### Q-Learning Memory")
    st.caption(
        "The engine learns Q-values per state/action pair. State is challenge_type:phase; "
        "action is provider:model."
    )
    q_rows = store.q_table()
    if q_rows:
        st.dataframe(q_rows, use_container_width=True)
        st.code(
            "Q(s,a) = Q(s,a) + alpha * (reward + gamma * maxQ(s_next) - Q(s,a))",
            language="text",
        )
        st.code(
            "Utility(a) = 0.62*Q + 0.23*prior + exploration_bonus - cost_penalty - risk_penalty",
            language="text",
        )
    else:
        st.info("No reinforcement memory yet. Run an episode with Q-learning enabled.")

    st.markdown("#### Agentic Algorithms")
    st.write(
        "- Goal-based agent: converts challenge type into weighted goals and evaluates success.\n"
        "- Utility-based agent: ranks models using expected utility, risk, local cost, and exploration.\n"
        "- Q-learning agent: updates long-term model policy memory after each episode.\n"
        "- UCB exploration: gives under-tested models a controlled chance to prove themselves."
    )

with tabs[4]:
    st.subheader("Saved Replays")
    episodes = store.list_episodes()
    if not episodes:
        st.info("No saved episodes yet.")
    for episode_info in episodes:
        with st.expander(f"{episode_info['title']} - Winner: {episode_info['winner']}"):
            episode = store.get_episode(str(episode_info["id"]))
            if not episode:
                continue
            st.write(episode.final_summary)
            st.json(episode.model_dump(mode="json"))

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")

st.markdown("<h1 style='text-align: center; color: blue;'>Impact of policy on Health outcomes</h1>", unsafe_allow_html=True)

# Health states
H1 = 0  # Healthy
H2 = 1  # Diseased
H3 = 2  # Dead

with st.sidebar:
    st.markdown("This app simulates the impact of new policies on health outcomes. \
                The user can adjust the parameters to see how the policy affects the prevalence of different \
                health states over time. The simulation is based on a simple model of disease progression \
                and does not take into account many real-world factors that would affect the outcome of a \
                policy change.")
    
    st.markdown("## Parameters")
    years = st.slider("Years", 2024, 2060, (2024, 2040))
    n_population = st.number_input("Population", 100000)
    new_policy_incidence_reduction_rate = st.slider("New Policy Incidence Reduction Rate", 0.0, 1.0, 0.2)

    P_incidence = st.number_input("Incidence Probability", 0.0, 1.0, 0.01)
    P_case_fatality = st.number_input("Case Fatality Probability", 0.0, 1.0, 0.005)
    P_mortality = st.number_input("Mortality Probability", 0.0, 1.0, 0.001)

    initial_disease_prevalence = st.number_input("Initial Disease Prevalence", 0.0, 1.0, 0.1)

    birth_rate = st.number_input("Birth Rate", 0.0, 1.0, 0.01)
    #death_rate = st.number_input("Death Rate", 0.0, 1.0, 0.01)

    run_simulation = st.button("Run Simulation")

if run_simulation:
    # Create array of years to simulate
    years = np.arange(years[0], years[1] + 1)

    # Policy scenarios: new policy reduces incidence by 20%
    P_incidence_policy = P_incidence * (1 - new_policy_incidence_reduction_rate)

    # Initial population states (all healthy)
    population_states = np.full(n_population, H1)

    # Published statistics for initial disease prevalence
    initial_disease_prevalence = 0.1  # 10% initially diseased

    # Assign initial disease status
    initial_diseased = np.random.rand(n_population) < initial_disease_prevalence
    population_states[initial_diseased] = H2

    # Update population with births and migration
    def update_population(population_states):
        birth_rate = 0.01  # 1% birth rate
        new_births = int(len(population_states) * birth_rate)
        new_population = np.full(new_births, H1)  # New births are healthy
        population_states = np.concatenate((population_states, new_population))
        return population_states, new_births

    # Remove deaths
    def remove_deaths(population_states):
        alive = population_states != H3
        dead = len(population_states) - np.sum(alive)
        population_states = population_states[alive]
        return population_states, dead

    # Simulation function
    def simulate_population(years, population_states, P_incidence, P_case_fatality, P_mortality):
        results = []
        stats = []
        for year in years:
            new_states = population_states.copy()
            n_healthy = np.sum(new_states == H1)
            n_diseased = np.sum(new_states == H2)
            n_dead = np.sum(new_states == H3)
            
            for i, state in enumerate(population_states):
                if state == H1:
                    if np.random.rand() < P_incidence:
                        new_states[i] = H2
                elif state == H2:
                    if np.random.rand() < P_case_fatality:
                        new_states[i] = H3
                    elif np.random.rand() < P_mortality:
                        new_states[i] = H3

            new_states, new_births = update_population(new_states)
            new_states, deaths = remove_deaths(new_states)
            
            stats.append({
                'Year': year,
                'Healthy': np.sum(new_states == H1),
                'Diseased': np.sum(new_states == H2),
                'Deaths': deaths,
                'Births': new_births,
                'Total Population': len(new_states)
            })
            
            results.append(new_states)
            population_states = new_states
        
        df_stats = pd.DataFrame(stats)
        return results, df_stats

    # Run simulations for business as usual and new policy
    results_bau, df_stats_bau = simulate_population(years, population_states, P_incidence, P_case_fatality, P_mortality)
    results_policy, df_stats_policy = simulate_population(years, population_states, P_incidence_policy, P_case_fatality, P_mortality)

    # Calculate prevalence
    def calculate_prevalence(results):
        prevalence_H1 = [np.mean(year == H1) * 100 for year in results]
        prevalence_H2 = [np.mean(year == H2) * 100 for year in results]
        prevalence_H3 = [np.mean(year == H3) * 100 for year in results]
        return prevalence_H1, prevalence_H2, prevalence_H3

    prevalence_bau_H1, prevalence_bau_H2, prevalence_bau_H3 = calculate_prevalence(results_bau)
    prevalence_policy_H1, prevalence_policy_H2, prevalence_policy_H3 = calculate_prevalence(results_policy)

    st.markdown("## Health State Prevalence Over Time")
    st.markdown("### Business as Usual")
    st.dataframe(df_stats_bau)

    # Plot stacked bar chart for BAU
    fig_bau = go.Figure()

    fig_bau.add_trace(go.Bar(x=df_stats_bau['Year'], y=df_stats_bau['Healthy'], name='Healthy', marker_color='green'))
    fig_bau.add_trace(go.Bar(x=df_stats_bau['Year'], y=df_stats_bau['Diseased'], name='Diseased', marker_color='orange'))
    fig_bau.add_trace(go.Bar(x=df_stats_bau['Year'], y=df_stats_bau['Deaths'], name='Dead', marker_color='red'))   
    #fig_bau.add_trace(go.Bar(x=df_stats_bau['Year'], y=df_stats_bau['Total Population'] - df_stats_bau['Healthy'] - df_stats_bau['Diseased'], name='Dead', marker_color='red'))

    fig_bau.update_layout(
        barmode='stack',
        title='Total Population (BAU) Over Time',
        xaxis_title='Year',
        yaxis_title='Population',
        legend=dict(x=0.01, y=0.99),
        template='plotly_white'
    )

    st.plotly_chart(fig_bau)

    st.markdown("### Policy")
    st.dataframe(df_stats_policy)

    # Plot stacked bar chart for Policy
    fig_policy = go.Figure()

    fig_policy.add_trace(go.Bar(x=df_stats_policy['Year'], y=df_stats_policy['Healthy'], name='Healthy', marker_color='green'))
    fig_policy.add_trace(go.Bar(x=df_stats_policy['Year'], y=df_stats_policy['Diseased'], name='Diseased', marker_color='orange'))
    fig_policy.add_trace(go.Bar(x=df_stats_policy['Year'], y=df_stats_policy['Deaths'], name='Dead', marker_color='red'))
    #fig_policy.add_trace(go.Bar(x=df_stats_policy['Year'], y=df_stats_policy['Total Population'] - df_stats_policy['Healthy'] - df_stats_policy['Diseased'], name='Dead', marker_color='red'))

    fig_policy.update_layout(
        barmode='stack',
        title='Total Population (Policy) Over Time',
        xaxis_title='Year',
        yaxis_title='Population',
        legend=dict(x=0.01, y=0.99),
        template='plotly_white'
    )

    st.plotly_chart(fig_policy)

    # Plot prevalence results using Plotly
    fig_prevalence = go.Figure()

    # Add traces for BAU
    fig_prevalence.add_trace(go.Scatter(x=years, y=prevalence_bau_H1, mode='lines', name='Healthy (BAU)', line=dict(dash='dash', color='green')))
    fig_prevalence.add_trace(go.Scatter(x=years, y=prevalence_bau_H2, mode='lines', name='Diseased (BAU)', line=dict(dash='dash', color='orange')))
    fig_prevalence.add_trace(go.Scatter(x=years, y=prevalence_bau_H3, mode='lines', name='Dead (BAU)', line=dict(dash='dash', color='red')))

    # Add traces for Policy
    fig_prevalence.add_trace(go.Scatter(x=years, y=prevalence_policy_H1, mode='lines', name='Healthy (Policy)', line=dict(color='green')))
    fig_prevalence.add_trace(go.Scatter(x=years, y=prevalence_policy_H2, mode='lines', name='Diseased (Policy)', line=dict(color='orange')))
    fig_prevalence.add_trace(go.Scatter(x=years, y=prevalence_policy_H3, mode='lines', name='Dead (Policy)', line=dict(color='red')))

    fig_prevalence.update_layout(
        title='Health State Prevalence Over Time',
        xaxis_title='Year',
        yaxis_title='Prevalence (%)',
        legend=dict(x=0.01, y=0.99),
        template='plotly_white'
    )

    st.plotly_chart(fig_prevalence)




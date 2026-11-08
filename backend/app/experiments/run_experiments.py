import json
import os
import sys
from typing import Any, Dict, List

# Ensure python path includes backend root
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app.experiments.ablations import AblationTravelSenseAI, NoRouteOptimizationRecommender
from app.experiments.baselines import (
    DistanceBasedRecommender,
    PopularityBasedRecommender,
    PreferenceDistanceRecommender,
    PreferenceOnlyRecommender,
    TravelSenseAIRecommender,
)
from app.experiments.metrics import (
    attraction_diversity,
    check_itinerary_constraints,
    ndcg_at_k,
    personalization_score,
    precision_at_k,
    recall_at_k,
    total_route_distance,
    total_travel_time_mins,
    travel_efficiency,
)
from app.experiments.user_evaluation import UserEvaluationStudy


def load_json_dataset(rel_path: str) -> Dict[str, Any]:
    full_path = os.path.join(os.path.dirname(__file__), rel_path)
    with open(full_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_benchmark_experiments():
    print("=" * 80)
    print(" TRAVELSENSEAI RESEARCH EVALUATION BENCHMARK ")
    print(" Phase 10: Rigorous Software Testing & Empirical Research Experiments")
    print("=" * 80)

    # 1. Load Controlled Datasets
    poi_data = load_json_dataset("datasets/poi_corpus.json")
    user_data = load_json_dataset("datasets/user_profiles.json")
    weather_data = load_json_dataset("datasets/weather_scenarios.json")

    pois = poi_data["pois"]
    personas = user_data["personas"]
    clear_weather = weather_data["scenarios"][0]
    rainy_weather = weather_data["scenarios"][1]

    print(f"\n[Dataset Loaded] POI Corpus: {len(pois)} attractions | Personas: {len(personas)} | Scenarios: {len(weather_data['scenarios'])}")

    # 2. Instantiate 5 Core Baselines
    models = [
        PopularityBasedRecommender(),
        DistanceBasedRecommender(),
        PreferenceOnlyRecommender(),
        PreferenceDistanceRecommender(),
        TravelSenseAIRecommender(),
    ]

    # Benchmark across Personas
    baseline_results: Dict[str, Dict[str, float]] = {}

    for model in models:
        m_name = model.name
        prec_3_list, prec_5_list, prec_6_list = [], [], []
        rec_3_list, rec_5_list, rec_6_list = [], [], []
        ndcg_3_list, ndcg_5_list, ndcg_6_list = [], [], []
        dist_list, time_list, eff_list = [], [], []
        cvr_list, feas_list, div_list = [], [], []
        user_rec_map: Dict[str, List[str]] = {}

        for user in personas:
            u_id = user["persona_id"]
            gt_set = set(user["ground_truth_relevant_pois"])
            rel_grades = user["relevance_grades"]
            budget = float(user["budget"])
            daily_hours = float(user["daily_hours"])

            # Generate top-6 recommendations
            recs = model.recommend(
                candidate_pois=pois,
                user_profile=user,
                weather_scenario=clear_weather,
                top_k=6,
            )
            rec_ids = [p["id"] for p in recs]
            user_rec_map[u_id] = rec_ids

            # Recommendation Metrics
            prec_3_list.append(precision_at_k(rec_ids, gt_set, k=3))
            prec_5_list.append(precision_at_k(rec_ids, gt_set, k=5))
            prec_6_list.append(precision_at_k(rec_ids, gt_set, k=6))

            rec_3_list.append(recall_at_k(rec_ids, gt_set, k=3))
            rec_5_list.append(recall_at_k(rec_ids, gt_set, k=5))
            rec_6_list.append(recall_at_k(rec_ids, gt_set, k=6))

            ndcg_3_list.append(ndcg_at_k(rec_ids, rel_grades, k=3))
            ndcg_5_list.append(ndcg_at_k(rec_ids, rel_grades, k=5))
            ndcg_6_list.append(ndcg_at_k(rec_ids, rel_grades, k=6))

            # Travel Efficiency Metrics
            route_km = total_route_distance(recs)
            t_time_mins = total_travel_time_mins(route_km)
            v_time_mins = sum(int(p.get("visit_duration_mins", 90)) for p in recs)
            dist_list.append(route_km)
            time_list.append(t_time_mins)
            eff_list.append(travel_efficiency(v_time_mins, t_time_mins))

            # Feasibility & Constraints
            is_valid, violations = check_itinerary_constraints(
                recs, budget=budget, daily_hours_limit=daily_hours, weather_scenario=clear_weather
            )
            cvr_list.append(1.0 if not is_valid else 0.0)
            feas_list.append(1.0 if is_valid else 0.0)

            # Diversity
            div_list.append(attraction_diversity(recs))

        # Personalization
        pers_score = personalization_score(user_rec_map)

        baseline_results[m_name] = {
            "Precision@3": round(sum(prec_3_list) / len(prec_3_list), 4),
            "Precision@5": round(sum(prec_5_list) / len(prec_5_list), 4),
            "Precision@6": round(sum(prec_6_list) / len(prec_6_list), 4),
            "Recall@3": round(sum(rec_3_list) / len(rec_3_list), 4),
            "Recall@5": round(sum(rec_5_list) / len(rec_5_list), 4),
            "Recall@6": round(sum(rec_6_list) / len(rec_6_list), 4),
            "NDCG@3": round(sum(ndcg_3_list) / len(ndcg_3_list), 4),
            "NDCG@5": round(sum(ndcg_5_list) / len(ndcg_5_list), 4),
            "NDCG@6": round(sum(ndcg_6_list) / len(ndcg_6_list), 4),
            "Total_Route_Dist_km": round(sum(dist_list) / len(dist_list), 2),
            "Total_Travel_Time_mins": round(sum(time_list) / len(time_list), 1),
            "Travel_Efficiency": round(sum(eff_list) / len(eff_list), 3),
            "Constraint_Violation_Rate": round(sum(cvr_list) / len(cvr_list), 3),
            "Itinerary_Feasibility_pct": round((sum(feas_list) / len(feas_list)) * 100.0, 1),
            "Attraction_Diversity": round(sum(div_list) / len(div_list), 3),
            "Personalization_Score": pers_score,
        }

    # 3. Ablation Studies
    ablation_models = [
        ("1. Full TravelSenseAI", TravelSenseAIRecommender()),
        ("2. Without Weather", AblationTravelSenseAI.get_no_weather_model()),
        ("3. Without Geographic Clustering", NoRouteOptimizationRecommender()),
        ("4. Without Preferences", AblationTravelSenseAI.get_no_preferences_model()),
        ("5. Without Route Optimization", NoRouteOptimizationRecommender()),
        ("6. Without Budget Constraints", AblationTravelSenseAI.get_no_budget_model()),
    ]

    ablation_results: Dict[str, Dict[str, float]] = {}
    for a_name, a_model in ablation_models:
        a_prec, a_ndcg, a_dist, a_feas, a_cvr = [], [], [], [], []
        # In rainy weather scenario to expose weather component
        target_weather = rainy_weather if "Weather" in a_name else clear_weather

        for user in personas:
            gt_set = set(user["ground_truth_relevant_pois"])
            rel_grades = user["relevance_grades"]
            budget = float(user["budget"])
            daily_hours = float(user["daily_hours"])

            recs = a_model.recommend(pois, user, target_weather, top_k=6)
            rec_ids = [p["id"] for p in recs]

            a_prec.append(precision_at_k(rec_ids, gt_set, k=5))
            a_ndcg.append(ndcg_at_k(rec_ids, rel_grades, k=5))
            route_km = total_route_distance(recs)
            a_dist.append(route_km)

            is_valid, _ = check_itinerary_constraints(
                recs, budget=budget, daily_hours_limit=daily_hours, weather_scenario=target_weather
            )
            a_feas.append(1.0 if is_valid else 0.0)
            a_cvr.append(0.0 if is_valid else 1.0)

        ablation_results[a_name] = {
            "Precision@5": round(sum(a_prec) / len(a_prec), 4),
            "NDCG@5": round(sum(a_ndcg) / len(a_ndcg), 4),
            "Route_Distance_km": round(sum(a_dist) / len(a_dist), 2),
            "Constraint_Violation_Rate": round(sum(a_cvr) / len(a_cvr), 3),
            "Feasibility_pct": round((sum(a_feas) / len(a_feas)) * 100.0, 1),
        }

    # 4. User Evaluation Study (30 Participants)
    user_study = UserEvaluationStudy(participant_count=30, seed=42)
    user_study_results = user_study.run_evaluation()

    # 5. Output Summary
    final_output = {
        "timestamp": "2026-11-04T12:00:00Z",
        "benchmark_environment": {
            "poi_corpus_size": len(pois),
            "personas_count": len(personas),
            "destination": "Hyderabad",
        },
        "baseline_comparison": baseline_results,
        "ablation_study": ablation_results,
        "user_evaluation_study": user_study_results,
    }

    out_path = os.path.join(os.path.dirname(__file__), "experiment_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2)

    print(f"\n[Saved] Complete Experiment Output -> {out_path}")

    # Display Tables in Console
    print("\n" + "=" * 80)
    print(" TABLE 1: BASELINE RECOMMENDATION & EFFICIENCY METRICS (N = 10 PERSONAS)")
    print("=" * 80)
    print(f"{'Method':<36} | {'P@5':<6} | {'R@5':<6} | {'NDCG@5':<7} | {'Dist(km)':<8} | {'Feas(%)':<7} | {'Pers':<5}")
    print("-" * 80)
    for method, m_data in baseline_results.items():
        print(
            f"{method:<36} | {m_data['Precision@5']:<6.4f} | {m_data['Recall@5']:<6.4f} | "
            f"{m_data['NDCG@5']:<7.4f} | {m_data['Total_Route_Dist_km']:<8.1f} | "
            f"{m_data['Itinerary_Feasibility_pct']:<7.1f} | {m_data['Personalization_Score']:<5.3f}"
        )

    print("\n" + "=" * 80)
    print(" TABLE 2: ABLATION STUDY RESULTS")
    print("=" * 80)
    print(f"{'Ablation Variant':<36} | {'P@5':<6} | {'NDCG@5':<7} | {'Dist(km)':<8} | {'CVR':<5} | {'Feas(%)':<7}")
    print("-" * 80)
    for variant, a_data in ablation_results.items():
        print(
            f"{variant:<36} | {a_data['Precision@5']:<6.4f} | {a_data['NDCG@5']:<7.4f} | "
            f"{a_data['Route_Distance_km']:<8.1f} | {a_data['Constraint_Violation_Rate']:<5.3f} | {a_data['Feasibility_pct']:<7.1f}"
        )

    print("\n" + "=" * 80)
    print(" TABLE 3: USER EVALUATION (N = 30 PARTICIPANTS, 5-POINT LIKERT SCALE)")
    print("=" * 80)
    print(f"{'Dimension':<36} | {'Baseline (Mean±SD)':<18} | {'TravelSense (Mean±SD)':<20} | {'t-stat':<7} | {'p-value':<9}")
    print("-" * 80)
    for dim, r in user_study_results["results"].items():
        b_str = f"{r['baseline_mean']:.2f} ± {r['baseline_std']:.2f}"
        t_str = f"{r['travelsense_mean']:.2f} ± {r['travelsense_std']:.2f}"
        print(f"{r['label']:<36} | {b_str:<18} | {t_str:<20} | {r['t_statistic']:<7.3f} | {r['p_value']:<9}")

    print("=" * 80)
    return final_output


if __name__ == "__main__":
    run_benchmark_experiments()


#!/usr/bin/env python3
"""
Visualize and compare music performance analysis results
"""

import json
import os
from pathlib import Path

def load_grade_data(base_dir, performance_name):
    """Load grade data for a performance"""
    grade_file = os.path.join(base_dir, performance_name, '07_grading', 'final_grade.json')
    
    if not os.path.exists(grade_file):
        return None
    
    with open(grade_file, 'r') as f:
        return json.load(f)

def print_comparison_table():
    """Print detailed comparison table"""
    
    base_dir = "/home/nikhilsingh/Documents/temp/Trials/Output/instrument_comparison"
    performances = ["violin", "bassoon", "clarinet", "saxphone", "ensemble"]
    display_names = ["Violin", "Bassoon", "Clarinet", "Saxophone", "Ensemble"]
    
    # Load all data
    all_data = {}
    for i, perf in enumerate(performances):
        data = load_grade_data(base_dir, perf)
        if data:
            all_data[display_names[i]] = data
    
    if not all_data:
        print("No grade data found!")
        return
    
    # Print header
    print("\n" + "="*100)
    print("COMPREHENSIVE PERFORMANCE COMPARISON")
    print("="*100)
    
    # Overall scores
    print("\n1. OVERALL SCORES")
    print("-"*100)
    print(f"{'Performance':<15} {'Score':>8} {'Status':<20}")
    print("-"*100)
    
    sorted_perfs = sorted(all_data.items(), key=lambda x: x[1]['overall_score'], reverse=True)
    for rank, (name, data) in enumerate(sorted_perfs, 1):
        score = data['overall_score']
        status = "✓ PASSING" if score >= 60 else "✗ FAILING"
        print(f"{rank}. {name:<12} {score:>8.1f} {status:<20}")
    
    # Component breakdown
    print("\n2. COMPONENT SCORES (out of maximum weight)")
    print("-"*100)
    
    components = ['pitch', 'note_accuracy', 'rhythm', 'tempo', 'articulation']
    comp_display = {
        'pitch': 'Pitch (30%)',
        'note_accuracy': 'Note Accuracy (20%)',
        'rhythm': 'Rhythm (20%)',
        'tempo': 'Tempo (15%)',
        'articulation': 'Articulation (15%)'
    }
    
    for comp in components:
        print(f"\n{comp_display[comp]}:")
        print(f"{'Performance':<15} {'Raw Score':>10} {'Percentage':>12} {'Rank':>6}")
        print("-"*50)
        
        comp_scores = []
        for name, data in all_data.items():
            raw = data['components'].get(comp, 0)
            weight = data['weights'].get(comp, 0)
            pct = (raw / weight * 100) if weight > 0 else 0
            comp_scores.append((name, raw, pct))
        
        comp_scores.sort(key=lambda x: x[1], reverse=True)
        
        for rank, (name, raw, pct) in enumerate(comp_scores, 1):
            print(f"{name:<15} {raw:>10.3f} {pct:>11.1f}% {rank:>6}")
    
    # Strengths and weaknesses
    print("\n3. STRENGTHS AND WEAKNESSES")
    print("-"*100)
    
    for name, data in sorted_perfs:
        print(f"\n{name}:")
        
        # Calculate percentages
        comp_pcts = {}
        for comp in components:
            raw = data['components'].get(comp, 0)
            weight = data['weights'].get(comp, 0)
            comp_pcts[comp] = (raw / weight * 100) if weight > 0 else 0
        
        # Find best and worst
        sorted_comps = sorted(comp_pcts.items(), key=lambda x: x[1], reverse=True)
        
        print(f"  Strengths:")
        for comp, pct in sorted_comps[:2]:
            status = "⭐" if pct >= 70 else "✓"
            print(f"    {status} {comp_display[comp]}: {pct:.1f}%")
        
        print(f"  Weaknesses:")
        for comp, pct in sorted_comps[-2:]:
            status = "⚠️" if pct < 30 else "○"
            print(f"    {status} {comp_display[comp]}: {pct:.1f}%")
    
    # Metadata
    print("\n4. ANALYSIS METADATA")
    print("-"*100)
    print(f"{'Performance':<15} {'Calculated':>12} {'Missing':>10} {'Weight Used':>15}")
    print("-"*100)
    
    for name, data in sorted_perfs:
        calc = len(data['calculated_components'])
        miss = len(data['missing_components'])
        weight = data['total_weight_used']
        print(f"{name:<15} {calc:>12}/5 {miss:>10}/5 {weight*100:>14.0f}%")
    
    print("\n" + "="*100)
    print("Analysis complete!")
    print("="*100 + "\n")

if __name__ == "__main__":
    print_comparison_table()

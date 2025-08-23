"""
Enhanced ISO Compliance Checking System
Advanced validation with scoring and corrective actions
"""

import logging
from typing import Dict, Any, Tuple, List, Optional

logger = logging.getLogger(__name__)


def check_enhanced_iso_compliance(test_data: Dict[str, Any]) -> Tuple[bool, float, Optional[str]]:
    """
    Enhanced ISO compliance check with scoring and corrective actions
    
    Returns:
        - is_compliant (bool): Overall compliance status
        - compliance_score (float): Score from 0-100
        - corrective_actions (str): Suggested corrective actions if non-compliant
    """
    
    violations = []
    scores = []
    corrective_actions = []
    
    # ISO 13006 - Dimensional checks with precise tolerances
    dimensional_score = check_dimensional_compliance(test_data, violations, corrective_actions)
    if dimensional_score is not None:
        scores.append(dimensional_score)
    
    # ISO 10545-3 - Water absorption
    water_absorption_score = check_water_absorption_compliance(test_data, violations, corrective_actions)
    if water_absorption_score is not None:
        scores.append(water_absorption_score)
    
    # ISO 10545-4 - Breaking strength
    breaking_strength_score = check_breaking_strength_compliance(test_data, violations, corrective_actions)
    if breaking_strength_score is not None:
        scores.append(breaking_strength_score)
    
    # ISO 10545-7 - Abrasion resistance (PEI)
    abrasion_score = check_abrasion_compliance(test_data, violations, corrective_actions)
    if abrasion_score is not None:
        scores.append(abrasion_score)
    
    # Visual defect severity impact
    defect_score = check_defect_compliance(test_data, violations, corrective_actions)
    if defect_score is not None:
        scores.append(defect_score)
    
    # Calculate overall compliance score
    if scores:
        compliance_score = sum(scores) / len(scores)
    else:
        compliance_score = 100.0  # No tests performed
    
    # Determine overall compliance (>= 85% required for PASS)
    is_compliant = compliance_score >= 85.0 and len(violations) == 0
    
    # Format corrective actions
    corrective_actions_text = None
    if corrective_actions:
        corrective_actions_text = "Actions correctives recommandées:\n" + "\n".join(f"• {action}" for action in corrective_actions)
    
    return is_compliant, compliance_score, corrective_actions_text


def check_dimensional_compliance(test_data: Dict[str, Any], violations: List[str], corrective_actions: List[str]) -> Optional[float]:
    """Check dimensional compliance according to ISO 13006"""
    
    scores = []
    
    # Warping check (≤0.6% for rectified tiles)
    warping = test_data.get('warping_percentage')
    if warping is not None:
        max_warping = 0.6
        if warping > max_warping:
            violations.append(f"Gauchissement ({warping}%) dépasse la limite ISO 13006 (≤{max_warping}%)")
            corrective_actions.append("Vérifier l'alignement des supports de cuisson et la planéité du four")
            scores.append(max(0, 100 - (warping - max_warping) * 50))
        else:
            scores.append(100)
    
    # Length, width, thickness tolerance (±0.5%)
    dimensions = ['length_mm', 'width_mm', 'thickness_mm']
    for dim in dimensions:
        value = test_data.get(dim)
        if value is not None:
            # Assuming nominal values for calculation (this would come from product spec in real system)
            tolerance_percent = 0.5
            if dim == 'thickness_mm':
                nominal = 10.0  # Example nominal thickness
            else:
                nominal = 300.0  # Example nominal length/width
            
            tolerance_absolute = nominal * tolerance_percent / 100
            deviation = abs(value - nominal)
            
            if deviation > tolerance_absolute:
                dim_name = dim.replace('_mm', '').replace('_', ' ').title()
                violations.append(f"{dim_name} ({value}mm) hors tolérance ISO 13006 (±{tolerance_percent}%)")
                corrective_actions.append(f"Ajuster les paramètres de pressage pour {dim_name.lower()}")
                scores.append(max(0, 100 - (deviation - tolerance_absolute) * 20))
            else:
                scores.append(100)
    
    return sum(scores) / len(scores) if scores else None


def check_water_absorption_compliance(test_data: Dict[str, Any], violations: List[str], corrective_actions: List[str]) -> Optional[float]:
    """Check water absorption compliance according to ISO 10545-3"""
    
    water_absorption = test_data.get('water_absorption_percentage')
    if water_absorption is not None:
        # For porcelain stoneware (grès cérame)
        max_absorption = 3.0
        
        if water_absorption > max_absorption:
            violations.append(f"Absorption d'eau ({water_absorption}%) dépasse la limite ISO 10545-3 (≤{max_absorption}% pour grès cérame)")
            corrective_actions.append("Augmenter la température de cuisson ou prolonger le cycle de cuisson")
            corrective_actions.append("Vérifier la composition de la pâte céramique")
            return max(0, 100 - (water_absorption - max_absorption) * 10)
        else:
            return 100
    
    return None


def check_breaking_strength_compliance(test_data: Dict[str, Any], violations: List[str], corrective_actions: List[str]) -> Optional[float]:
    """Check breaking strength compliance according to ISO 10545-4"""
    
    breaking_strength = test_data.get('breaking_strength_n')
    if breaking_strength is not None:
        # Minimum for floor tiles
        min_strength = 1300
        
        if breaking_strength < min_strength:
            violations.append(f"Résistance à la rupture ({breaking_strength}N) inférieure à la norme ISO 10545-4 (≥{min_strength}N)")
            corrective_actions.append("Optimiser la formulation de la pâte pour améliorer la résistance mécanique")
            corrective_actions.append("Vérifier et ajuster les paramètres de cuisson")
            return max(0, (breaking_strength / min_strength) * 100)
        else:
            return 100
    
    return None


def check_abrasion_compliance(test_data: Dict[str, Any], violations: List[str], corrective_actions: List[str]) -> Optional[float]:
    """Check abrasion resistance compliance according to ISO 10545-7"""
    
    abrasion_pei = test_data.get('abrasion_resistance_pei')
    if abrasion_pei is not None:
        # PEI rating should be appropriate for intended use
        if abrasion_pei < 1 or abrasion_pei > 5:
            violations.append(f"Classification PEI ({abrasion_pei}) invalide (doit être entre 1 et 5)")
            corrective_actions.append("Effectuer un nouveau test d'abrasion selon la norme ISO 10545-7")
            return 0
        else:
            # Score based on PEI rating (higher is better for commercial use)
            return min(100, abrasion_pei * 20)
    
    return None


def check_defect_compliance(test_data: Dict[str, Any], violations: List[str], corrective_actions: List[str]) -> Optional[float]:
    """Check visual defect compliance with severity consideration"""
    
    defect_type = test_data.get('defect_type', 'none')
    defect_count = test_data.get('defect_count', 0)
    defect_severity = test_data.get('defect_severity', 'minor')
    
    if defect_type != 'none' and defect_count > 0:
        # Severity impact on scoring
        severity_multipliers = {
            'minor': 1.0,
            'major': 2.5,
            'critical': 5.0
        }
        
        multiplier = severity_multipliers.get(defect_severity, 1.0)
        effective_defect_count = defect_count * multiplier
        
        # Define acceptable defect thresholds
        if defect_severity == 'critical' and defect_count > 0:
            violations.append(f"Défauts critiques détectés: {defect_count} x {defect_type}")
            corrective_actions.append("Isoler le lot et procéder à un tri qualité complet")
            corrective_actions.append("Analyser les causes racines des défauts critiques")
            return 0
        elif effective_defect_count > 5:
            defect_name = defect_type.replace('_', ' ').title()
            violations.append(f"Nombre excessif de défauts {defect_severity}: {defect_count} x {defect_name}")
            corrective_actions.append(f"Réduire les défauts de type {defect_name}")
            if 'crack' in defect_type or 'chip' in defect_type:
                corrective_actions.append("Vérifier les conditions de manutention et transport")
            elif 'glaze' in defect_type:
                corrective_actions.append("Contrôler l'application et la cuisson de l'émail")
            return max(20, 100 - effective_defect_count * 10)
        else:
            # Minor defects acceptable within limits
            return max(70, 100 - effective_defect_count * 5)
    
    return 100  # No defects


# Legacy function for backward compatibility
def check_iso_compliance(test_data: Dict[str, Any]) -> bool:
    """Legacy ISO compliance check for backward compatibility"""
    is_compliant, _, _ = check_enhanced_iso_compliance(test_data)
    return is_compliant
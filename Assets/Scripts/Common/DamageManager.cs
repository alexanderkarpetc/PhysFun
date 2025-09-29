
using UnityEngine;

public static class DamageManager
{
    public static int CalculateImpactDamage(float relSpeed, float mass, bool playerIsBelow)
    {
        var koef = playerIsBelow ? 1f : 0.5f;
        koef /= 5f; // balance
        
        var damage = relSpeed * mass * koef;
        
        Debug.Log($"Damage calc: speed={relSpeed:F1}, mass={mass:F1}, below={playerIsBelow}, damage={damage:F1}");
        return Mathf.CeilToInt(damage);
    }
}
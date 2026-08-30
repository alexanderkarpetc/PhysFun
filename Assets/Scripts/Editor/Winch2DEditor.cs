using Props;
using UnityEditor;
using UnityEngine;

namespace Editor
{
    /// <summary>
    /// Shows what the cable is actually doing, and shouts about the setups that fail quietly.
    ///
    /// A winch that does not move looks the same whatever the reason — a load that is not dynamic,
    /// a cable already wound in to its limit, a rope too short to pay out, nothing driving the
    /// motor. None of those throw. So they are all checked here, and in play mode the live numbers
    /// say which part of the chain has stopped.
    /// </summary>
    [CustomEditor(typeof(Winch2D))]
    public sealed class Winch2DEditor : UnityEditor.Editor
    {
        public override bool RequiresConstantRepaint() => Application.isPlaying;

        public override void OnInspectorGUI()
        {
            var winch = (Winch2D)target;

            DrawDefaultInspector();
            EditorGUILayout.Space();

            if (Application.isPlaying) DrawLive(winch);
            else DrawChecks(winch);
        }

        private static void DrawLive(Winch2D winch)
        {
            EditorGUILayout.LabelField("Running", EditorStyles.boldLabel);
            using (new EditorGUI.DisabledScope(true))
            {
                EditorGUILayout.Toggle("Engaged", winch.Engaged);
                EditorGUILayout.FloatField("Motor input", winch.MotorInput);
                EditorGUILayout.FloatField("Cable length", winch.cableLength);
                EditorGUILayout.FloatField("Side A length", winch.SideALength);
                EditorGUILayout.FloatField("Pay-out rate", winch.SideARate);
                EditorGUILayout.FloatField("Tension (N)", winch.Tension);
                if (winch.loadA) EditorGUILayout.Toggle("Load awake", winch.loadA.IsAwake());
                if (winch.ropeA) EditorGUILayout.Toggle("Rope A intact", winch.ropeA.IsIntact);
            }

            if (!winch.Engaged)
                EditorGUILayout.HelpBox("Let go of the load — the cable parted or Release() was called.",
                                        MessageType.Warning);
            else if (winch.cableLength <= winch.minLength + 0.001f)
                EditorGUILayout.HelpBox("Wound in to Min Length. It will not haul any further.",
                                        MessageType.Info);
            else if (winch.cableLength >= winch.maxLength - 0.001f)
                EditorGUILayout.HelpBox("Payed out to Max Length. It will not lower any further.",
                                        MessageType.Info);

            EditorGUILayout.Space();
            EditorGUILayout.LabelField("Hold to drive, ignoring whatever normally controls it:");
            using (new EditorGUILayout.HorizontalScope())
            {
                if (GUILayout.RepeatButton("Haul in")) winch.MotorInput = 1f;
                if (GUILayout.RepeatButton("Pay out")) winch.MotorInput = -1f;
            }
        }

        private static void DrawChecks(Winch2D winch)
        {
            if (!winch.loadA)
            {
                EditorGUILayout.HelpBox("Load A is empty. Nothing to pull.", MessageType.Error);
                return;
            }

            if (winch.loadA.bodyType != RigidbodyType2D.Dynamic)
                EditorGUILayout.HelpBox($"Load A is {winch.loadA.bodyType}. A cable can only move a " +
                                        "Dynamic body — it will pull and nothing will happen.",
                                        MessageType.Error);

            if (!winch.motorized && !winch.loadB)
                EditorGUILayout.HelpBox("Not motorised and no Load B, so nothing ever changes the " +
                                        "cable length. Tick Motorized, or fill Load B for a balance.",
                                        MessageType.Warning);

            if (winch.motorized && !winch.GetComponent<WinchInput2D>())
                EditorGUILayout.HelpBox("Motorised, but nothing on this object drives MotorInput. " +
                                        "Add a Winch Input, or set winch.MotorInput from your own code.",
                                        MessageType.Info);

            Transform pulley = winch.pulleyA ? winch.pulleyA : winch.transform;
            float run = Vector2.Distance(winch.loadA.transform.TransformPoint(winch.hookA), pulley.position);

            // Hook is given in the load's own space; world coordinates land it somewhere absurd.
            var bounds = winch.loadA.GetComponent<Collider2D>();
            if (bounds && winch.hookA.magnitude > bounds.bounds.size.magnitude * 2f)
                EditorGUILayout.HelpBox("Hook A sits far outside the load. It is a local offset " +
                                        "inside Load A, not a world position.", MessageType.Warning);

            if (winch.maxLength < run - 0.01f)
                EditorGUILayout.HelpBox($"The load already hangs {run:0.00} m out, past Max Length " +
                                        $"({winch.maxLength:0.00}). It will be yanked in on the first step.",
                                        MessageType.Warning);

            if (winch.ropeA && winch.loadB == null)
            {
                float ropeLen = winch.ropeA.PathLength();
                if (ropeLen < winch.maxLength - 0.01f)
                    EditorGUILayout.HelpBox($"Rope A is {ropeLen:0.00} m but the cable pays out to " +
                                            $"{winch.maxLength:0.00} m. Build the rope with the load " +
                                            "at the bottom of its travel, or lower Max Length.",
                                            MessageType.Warning);
            }

            EditorGUILayout.HelpBox($"Cable runs {run:0.00} m, between {winch.minLength:0.00} and " +
                                    $"{winch.maxLength:0.00}.\n" +
                                    (winch.breakTension > 0f
                                        ? $"Parts at {winch.breakTension:0} N — about " +
                                          $"{winch.breakTension / 9.81f:0} kg hung still."
                                        : "Never parts under load."),
                                    MessageType.None);
        }
    }
}

// The darkness over everything the player has not seen, for Vision.FogOfWar.
//
// _MainTex is one byte per fog cell (0 = never seen, 1 = fully seen) covering the quad.
// Each fragment is snapped to the art-pixel grid first, so the fog edge steps in whole art
// pixels like the rest of the world instead of being a smooth screen-space gradient. Then a
// 3x3 tent over bilinear taps softens the cells, and a smoothstep keeps the dark properly
// dark and the seen properly clear, with the soft band in between.
// Lives under Resources so the runtime-created material survives a build.
Shader "PhysFun/FogOfWar"
{
    Properties
    {
        [HideInInspector] _MainTex ("Seen", 2D) = "black" {}
        _Color ("Fog", Color) = (0.02, 0.016, 0.027, 1)
        _Origin ("World origin of the quad", Vector) = (0, 0, 0, 0)
        _Size ("World size of the quad", Vector) = (1, 1, 0, 0)
        _ArtPPU ("Art pixels per unit", Float) = 20
        _Blur ("Blur, in cells", Float) = 1
    }

    SubShader
    {
        Tags
        {
            "Queue" = "Transparent"
            "RenderType" = "Transparent"
            "IgnoreProjector" = "True"
            "PreviewType" = "Plane"
        }

        Blend SrcAlpha OneMinusSrcAlpha
        Cull Off
        Lighting Off
        ZWrite Off
        ZTest Always

        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"

            sampler2D _MainTex;
            float4 _MainTex_TexelSize;
            fixed4 _Color;
            float4 _Origin;
            float4 _Size;
            float _ArtPPU;
            float _Blur;

            struct appdata
            {
                float4 vertex : POSITION;
            };

            struct v2f
            {
                float4 pos   : SV_POSITION;
                float2 world : TEXCOORD0;
            };

            v2f vert(appdata v)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(v.vertex);
                o.world = mul(unity_ObjectToWorld, v.vertex).xy;
                return o;
            }

            fixed4 frag(v2f i) : SV_Target
            {
                float2 wp = (floor(i.world * _ArtPPU) + 0.5) / _ArtPPU;
                float2 uv = (wp - _Origin.xy) / _Size.xy;
                float2 t = _MainTex_TexelSize.xy * _Blur;

                float v = tex2D(_MainTex, uv).r * 4.0
                        + (tex2D(_MainTex, uv + float2( t.x, 0)).r
                         + tex2D(_MainTex, uv + float2(-t.x, 0)).r
                         + tex2D(_MainTex, uv + float2(0,  t.y)).r
                         + tex2D(_MainTex, uv + float2(0, -t.y)).r) * 2.0
                        + (tex2D(_MainTex, uv + float2( t.x,  t.y)).r
                         + tex2D(_MainTex, uv + float2(-t.x,  t.y)).r
                         + tex2D(_MainTex, uv + float2( t.x, -t.y)).r
                         + tex2D(_MainTex, uv + float2(-t.x, -t.y)).r);
                v /= 16.0;

                float dark = 1.0 - smoothstep(0.05, 0.95, v);
                return fixed4(_Color.rgb, dark * _Color.a);
            }
            ENDCG
        }
    }
}

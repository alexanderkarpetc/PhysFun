// The light over the world, for Lighting.LightField.
//
// _MainTex is the light grid, one texel per light cell covering the quad, holding half the
// light (0.5 = the art as drawn). It is laid over the frame as a 2x multiply - dst * src * 2 -
// so the same map can darken the unlit cave and brighten and tint the wall next to a lamp.
// Each fragment is snapped to the art-pixel grid first, so light steps in whole art pixels like
// everything else, then sampled bilinearly; a 4x4 ordered dither of a quarter step keeps the
// slow falloff of a big light from banding.
// Lives under Resources so the runtime-created material survives a build.
Shader "PhysFun/LightMap"
{
    Properties
    {
        [HideInInspector] _MainTex ("Light", 2D) = "grey" {}
        _Origin ("World origin of the quad", Vector) = (0, 0, 0, 0)
        _Size ("World size of the quad", Vector) = (1, 1, 0, 0)
        _ArtPPU ("Art pixels per unit", Float) = 20
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

        Blend DstColor SrcColor
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
            float4 _Origin;
            float4 _Size;
            float _ArtPPU;

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

            static const float Bayer[16] =
            {
                0, 8, 2, 10,
                12, 4, 14, 6,
                3, 11, 1, 9,
                15, 7, 13, 5
            };

            fixed4 frag(v2f i) : SV_Target
            {
                float2 art = floor(i.world * _ArtPPU);
                float2 wp = (art + 0.5) / _ArtPPU;
                float3 l = tex2D(_MainTex, (wp - _Origin.xy) / _Size.xy).rgb;

                int2 d = int2(fmod(fmod(art, 4.0) + 4.0, 4.0));
                l += (Bayer[d.y * 4 + d.x] / 16.0 - 0.5) / 255.0 * 4.0;
                return fixed4(saturate(l), 1);
            }
            ENDCG
        }
    }
}

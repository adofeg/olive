uniform sampler2D tex_in;
uniform vec4 color_in;
uniform float saturation_in;
uniform float strength_in;
uniform bool preserve_luminosity_in;

in vec2 ove_texcoord;
out vec4 frag_color;

vec3 rgb_to_hsl(vec3 c) {
  float max_c = max(c.r, max(c.g, c.b));
  float min_c = min(c.r, min(c.g, c.b));
  float l = (max_c + min_c) * 0.5;

  if (abs(max_c - min_c) < 1e-6) {
    return vec3(0.0, 0.0, l);
  }

  float d = max_c - min_c;
  float s = l > 0.5 ? d / (2.0 - max_c - min_c) : d / (max_c + min_c);

  float h;
  if (max_c == c.r) {
    h = (c.g - c.b) / d + (c.g < c.b ? 6.0 : 0.0);
  } else if (max_c == c.g) {
    h = (c.b - c.r) / d + 2.0;
  } else {
    h = (c.r - c.g) / d + 4.0;
  }
  h /= 6.0;

  return vec3(h, s, l);
}

vec3 hsl_to_rgb(vec3 hsl) {
  if (hsl.y == 0.0) {
    return vec3(hsl.z);
  }

  float q = hsl.z < 0.5
    ? hsl.z * (1.0 + hsl.y)
    : hsl.z + hsl.y - hsl.z * hsl.y;
  float p = 2.0 * hsl.z - q;

  vec3 t = fract(vec3(hsl.x + 1.0/3.0, hsl.x, hsl.x - 1.0/3.0));
  vec3 rgb;
  for (int i = 0; i < 3; i++) {
    float ti = t[i];
    if (ti < 1.0/6.0) rgb[i] = p + (q - p) * 6.0 * ti;
    else if (ti < 0.5) rgb[i] = q;
    else if (ti < 2.0/3.0) rgb[i] = p + (q - p) * (2.0/3.0 - ti) * 6.0;
    else rgb[i] = p;
  }
  return rgb;
}

void main() {
  vec4 col = texture(tex_in, ove_texcoord);
  vec3 target_hsl = rgb_to_hsl(color_in.rgb);

  float l = preserve_luminosity_in
    ? dot(col.rgb, vec3(0.299, 0.587, 0.114))
    : target_hsl.z;

  vec3 colorized = hsl_to_rgb(vec3(target_hsl.x, target_hsl.y * saturation_in, l));
  vec3 result = mix(col.rgb, colorized, strength_in);

  frag_color = vec4(result, col.a);
}

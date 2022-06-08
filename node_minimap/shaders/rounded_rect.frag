#version 330
in float Aspect;
smooth in vec2 UV;
flat in vec4 Color;
out vec4 fragColor;

//---------------------------------------------------------
// draw rounded rectangle
//---------------------------------------------------------
float roundedRectangle (vec2 pos, vec2 size, float radius)
{
  size = size - vec2(radius);
  return length(max(abs(pos), size) - size) - radius;
}

void main()
{
  // Scale factor of the rectangle
  float size = 0.49;
  float dist = roundedRectangle(UV - vec2(0.5 * Aspect, 0.5), vec2(size * Aspect, size), 0.1);

  // Width of the outline
  float line_width = 0.012;
  if (dist > line_width) {
    discard;
  }

  // Add outline on top of base color
  float outline = smoothstep(line_width, 0., abs(dist)); 
  fragColor = vec4(outline);
  vec4 color = dist > 0 ? vec4(0.0) : Color;
  fragColor = (color + outline);

  // fragColor = blender_srgb_to_framebuffer_space(fragColor);
}
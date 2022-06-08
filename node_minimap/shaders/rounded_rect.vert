#version 330
uniform mat4 ModelViewProjectionMatrix;
uniform float aspect;
uniform vec4 color;

in vec2 pos;
in vec2 uv;

smooth out vec2 UV;
flat out vec4 Color;
out float Aspect;

void main() {
  gl_Position = ModelViewProjectionMatrix * vec4(pos, 0.0, 1.0);
  UV = uv;
  Aspect = aspect;
  Color = color;
}
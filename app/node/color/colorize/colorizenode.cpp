/***

  Olive - Non-Linear Video Editor
  Copyright (C) 2022 Olive Team

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <http://www.gnu.org/licenses/>.

***/

#include "colorizenode.h"

#include "common/filefunctions.h"
#include "widget/slider/floatslider.h"

namespace olive {

const QString ColorizeNode::kTextureInput = QStringLiteral("tex_in");
const QString ColorizeNode::kColorInput = QStringLiteral("color_in");
const QString ColorizeNode::kSaturationInput = QStringLiteral("saturation_in");
const QString ColorizeNode::kStrengthInput = QStringLiteral("strength_in");
const QString ColorizeNode::kPreserveLuminosityInput = QStringLiteral("preserve_luminosity_in");

#define super Node

ColorizeNode::ColorizeNode()
{
  AddInput(kTextureInput, NodeValue::kTexture, InputFlags(kInputFlagNotKeyframable));

  AddInput(kColorInput, NodeValue::kColor, QVariant::fromValue(Color(0.5f, 0.5f, 0.5f, 1.0f)));

  AddInput(kSaturationInput, NodeValue::kFloat, 0.5);
  SetInputProperty(kSaturationInput, QStringLiteral("view"), FloatSlider::kPercentage);
  SetInputProperty(kSaturationInput, QStringLiteral("min"), 0.0);
  SetInputProperty(kSaturationInput, QStringLiteral("max"), 1.0);

  AddInput(kStrengthInput, NodeValue::kFloat, 1.0);
  SetInputProperty(kStrengthInput, QStringLiteral("view"), FloatSlider::kPercentage);
  SetInputProperty(kStrengthInput, QStringLiteral("min"), 0.0);
  SetInputProperty(kStrengthInput, QStringLiteral("max"), 1.0);

  AddInput(kPreserveLuminosityInput, NodeValue::kBoolean, true);

  SetFlag(kVideoEffect);
  SetEffectInput(kTextureInput);
}

QString ColorizeNode::Name() const
{
  return tr("Colorize");
}

QString ColorizeNode::id() const
{
  return QStringLiteral("org.olivevideoeditor.Olive.colorize");
}

QVector<Node::CategoryID> ColorizeNode::Category() const
{
  return {kCategoryColor};
}

QString ColorizeNode::Description() const
{
  return tr("Colorize a grayscale or desaturated image with a target color.");
}

void ColorizeNode::Retranslate()
{
  super::Retranslate();

  SetInputName(kTextureInput, tr("Input"));
  SetInputName(kColorInput, tr("Color"));
  SetInputName(kSaturationInput, tr("Saturation"));
  SetInputName(kStrengthInput, tr("Strength"));
  SetInputName(kPreserveLuminosityInput, tr("Preserve Luminosity"));
}

void ColorizeNode::Value(const NodeValueRow &value, const NodeGlobals &globals, NodeValueTable *table) const
{
  if (TexturePtr tex = value[kTextureInput].toTexture()) {
    double strength = value[kStrengthInput].toDouble();
    if (strength <= 0.0) {
      table->Push(value[kTextureInput]);
      return;
    }

    table->Push(NodeValue::kTexture, tex->toJob(ShaderJob(value)), this);
  }
}

ShaderCode ColorizeNode::GetShaderCode(const ShaderRequest &request) const
{
  Q_UNUSED(request)
  return ShaderCode(FileFunctions::ReadFileAsString(QStringLiteral(":/shaders/colorize.frag")));
}

}

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

#include "testutil.h"

#include "node/distort/crop/cropdistortnode.h"
#include "node/distort/transform/transformdistortnode.h"
#include "node/generator/solid/solid.h"
#include "node/math/merge/merge.h"

namespace olive {

OLIVE_ADD_TEST(SolidGenerator_Creation) {
  SolidGenerator node;

  OLIVE_ASSERT_EQUAL(node.id(), QStringLiteral("org.olivevideoeditor.Olive.solid"));
  OLIVE_ASSERT(node.HasInputWithID(SolidGenerator::kColorInput));

  OLIVE_TEST_END;
}

OLIVE_ADD_TEST(SolidGenerator_DefaultColor) {
  SolidGenerator node;

  Color default_color = node.GetStandardValue(SolidGenerator::kColorInput).value<Color>();
  OLIVE_ASSERT(default_color.red() > 0.0f || default_color.green() > 0.0f || default_color.blue() > 0.0f);
  OLIVE_ASSERT_EQUAL(default_color.alpha(), 1.0f);

  OLIVE_TEST_END;
}

OLIVE_ADD_TEST(CropDistortNode_Creation) {
  CropDistortNode node;

  OLIVE_ASSERT_EQUAL(node.id(), QStringLiteral("org.olivevideoeditor.Olive.crop"));
  OLIVE_ASSERT(node.HasInputWithID(CropDistortNode::kTextureInput));

  OLIVE_TEST_END;
}

OLIVE_ADD_TEST(MergeNode_Creation) {
  MergeNode node;

  OLIVE_ASSERT_EQUAL(node.id(), QStringLiteral("org.olivevideoeditor.Olive.merge"));
  OLIVE_ASSERT(node.HasInputWithID(MergeNode::kTextureInput));
  OLIVE_ASSERT(node.HasInputWithID(MergeNode::kParamAIn));
  OLIVE_ASSERT(node.HasInputWithID(MergeNode::kParamBIn));

  OLIVE_TEST_END;
}

OLIVE_ADD_TEST(TransformDistortNode_Creation) {
  TransformDistortNode node;

  OLIVE_ASSERT_EQUAL(node.id(), QStringLiteral("org.olivevideoeditor.Olive.transform"));
  OLIVE_ASSERT(node.HasInputWithID(TransformDistortNode::kTextureInput));
  OLIVE_ASSERT(node.HasInputWithID(TransformDistortNode::kPositionInput));
  OLIVE_ASSERT(node.HasInputWithID(TransformDistortNode::kRotationInput));
  OLIVE_ASSERT(node.HasInputWithID(TransformDistortNode::kScaleInput));

  OLIVE_TEST_END;
}

}

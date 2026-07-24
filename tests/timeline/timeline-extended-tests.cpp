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

#include "node/block/clip/clip.h"
#include "node/block/transition/crossdissolve/crossdissolvetransition.h"
#include "node/color/colorize/colorizenode.h"
#include "node/effect/opacity/opacityeffect.h"
#include "node/factory.h"
#include "node/project.h"
#include "node/project/sequence/sequence.h"
#include "testutil.h"
#include "timeline/timelineundogeneral.h"
#include "timeline/timelineundopointer.h"
#include "undo/undocommand.h"

namespace olive {

#define TIMELINE_TEST_START \
  Project project; \
  Sequence sequence; \
  sequence.setParent(&project); \
  ColorManager::SetUpDefaultConfig()

OLIVE_ADD_TEST(EffectOnClip) {
  TIMELINE_TEST_START;

  Track *track = sequence.GetTracks().first();

  // Create a clip
  ClipBlock *clip = new ClipBlock();
  clip->set_length_and_media_out(100);
  clip->setParent(&project);
  track->AppendBlock(clip);

  // Create opacity effect
  OpacityEffect *opacity = new OpacityEffect();
  opacity->setParent(&project);

  // Connect effect to clip: clip.buffer_in -> opacity
  Node::ConnectEdge(opacity, NodeInput(clip, QStringLiteral("buffer_in")));

  // Verify connection
  OLIVE_ASSERT(clip->GetConnectedOutput(QStringLiteral("buffer_in")) == opacity);

  // Verify that the track still has the clip
  OLIVE_ASSERT(static_cast<int>(track->Blocks().size()) == 1 && track->Blocks().first() == clip);

  OLIVE_TEST_END;
}

OLIVE_ADD_TEST(CrossDissolveBetweenClips) {
  TIMELINE_TEST_START;

  Track *track = sequence.GetTracks().first();

  // Create two clips
  ClipBlock *clip_a = new ClipBlock();
  clip_a->set_length_and_media_out(50);
  clip_a->setParent(&project);
  track->AppendBlock(clip_a);

  ClipBlock *clip_b = new ClipBlock();
  clip_b->set_length_and_media_out(50);
  clip_b->setParent(&project);
  track->AppendBlock(clip_b);

  // Create cross dissolve transition
  CrossDissolveTransition *transition = new CrossDissolveTransition();
  transition->setParent(&project);
  transition->set_length_and_media_out(15);

  // Connect transition to both clips (outgoing and incoming)
  Node::ConnectEdge(clip_a, NodeInput(transition, QStringLiteral("out_block_in")));
  Node::ConnectEdge(clip_b, NodeInput(transition, QStringLiteral("in_block_in")));

  // Verify connections
  OLIVE_ASSERT(transition->GetConnectedOutput(QStringLiteral("out_block_in")) == clip_a);
  OLIVE_ASSERT(transition->GetConnectedOutput(QStringLiteral("in_block_in")) == clip_b);

  // Blocks should include transition
  OLIVE_ASSERT(static_cast<int>(track->Blocks().size()) == 3);

  OLIVE_TEST_END;
}

OLIVE_ADD_TEST(ColorizeEffect_Defaults) {
  TIMELINE_TEST_START;

  ColorizeNode *colorize = new ColorizeNode();
  colorize->setParent(&project);

  // Verify default values
  OLIVE_ASSERT_EQUAL(colorize->GetStandardValue(ColorizeNode::kSaturationInput).toDouble(), 0.5);
  OLIVE_ASSERT_EQUAL(colorize->GetStandardValue(ColorizeNode::kStrengthInput).toDouble(), 1.0);
  OLIVE_ASSERT(colorize->GetStandardValue(ColorizeNode::kPreserveLuminosityInput).toBool());
  Color default_color = colorize->GetStandardValue(ColorizeNode::kColorInput).value<Color>();
  OLIVE_ASSERT_EQUAL(default_color.red(), 0.5f);

  // Change and verify
  colorize->SetStandardValue(ColorizeNode::kSaturationInput, 0.75);
  OLIVE_ASSERT_EQUAL(colorize->GetStandardValue(ColorizeNode::kSaturationInput).toDouble(), 0.75);

  OLIVE_TEST_END;
}

OLIVE_ADD_TEST(ColorizeEffect_OnClip) {
  TIMELINE_TEST_START;

  Track *track = sequence.GetTracks().first();

  ClipBlock *clip = new ClipBlock();
  clip->set_length_and_media_out(100);
  clip->setParent(&project);
  track->AppendBlock(clip);

  // Create Colorize effect and connect to clip
  ColorizeNode *colorize = new ColorizeNode();
  colorize->setParent(&project);

  Node::ConnectEdge(colorize, NodeInput(clip, QStringLiteral("buffer_in")));

  // Verify connection
  OLIVE_ASSERT(clip->GetConnectedOutput(QStringLiteral("buffer_in")) == colorize);

  // Verify clip still on track
  OLIVE_ASSERT(static_cast<int>(track->Blocks().size()) == 1);
  OLIVE_ASSERT(track->Blocks().first() == clip);

  OLIVE_TEST_END;
}

}

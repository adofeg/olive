#include "testutil.h"

#include "node/color/colorize/colorizenode.h"
#include "node/factory.h"
#include "node/keying/chromakey/chromakey.h"
#include "node/node.h"

namespace olive {

OLIVE_ADD_TEST(ColorizeNode_Creation) {
  ColorizeNode node;

  OLIVE_ASSERT_EQUAL(node.id(), QStringLiteral("org.olivevideoeditor.Olive.colorize"));
  OLIVE_ASSERT_EQUAL(node.Name(), QStringLiteral("Colorize"));
  OLIVE_ASSERT(!node.Category().isEmpty());

  OLIVE_TEST_END;
}

OLIVE_ADD_TEST(ColorizeNode_Inputs) {
  ColorizeNode node;

  // Verify all expected inputs exist
  OLIVE_ASSERT(node.HasInputWithID(ColorizeNode::kTextureInput));
  OLIVE_ASSERT(node.HasInputWithID(ColorizeNode::kColorInput));
  OLIVE_ASSERT(node.HasInputWithID(ColorizeNode::kSaturationInput));
  OLIVE_ASSERT(node.HasInputWithID(ColorizeNode::kStrengthInput));
  OLIVE_ASSERT(node.HasInputWithID(ColorizeNode::kPreserveLuminosityInput));

  // Check defaults
  OLIVE_ASSERT_EQUAL(node.GetStandardValue(ColorizeNode::kSaturationInput).toDouble(), 0.5);
  OLIVE_ASSERT_EQUAL(node.GetStandardValue(ColorizeNode::kStrengthInput).toDouble(), 1.0);
  OLIVE_ASSERT(node.GetStandardValue(ColorizeNode::kPreserveLuminosityInput).toBool());

  OLIVE_TEST_END;
}

OLIVE_ADD_TEST(ColorizeNode_ShaderCode) {
  ColorizeNode node;

  ShaderCode code = node.GetShaderCode({QString()});
  OLIVE_ASSERT(!code.frag_code().isEmpty());

  OLIVE_TEST_END;
}

OLIVE_ADD_TEST(ColorizeNode_FactoryRegistration) {
  NodeFactory::Initialize();

  Node* created = NodeFactory::CreateFromID(QStringLiteral("org.olivevideoeditor.Olive.colorize"));
  OLIVE_ASSERT(created != nullptr);
  OLIVE_ASSERT_EQUAL(created->id(), QStringLiteral("org.olivevideoeditor.Olive.colorize"));

  delete created;
  NodeFactory::Destroy();

  OLIVE_TEST_END;
}

OLIVE_ADD_TEST(ChromaKeyNode_Inputs) {
  ChromaKeyNode node;

  OLIVE_ASSERT(node.HasInputWithID(ChromaKeyNode::kColorInput));
  OLIVE_ASSERT(node.HasInputWithID(ChromaKeyNode::kLowerToleranceInput));
  OLIVE_ASSERT(node.HasInputWithID(ChromaKeyNode::kUpperToleranceInput));
  OLIVE_ASSERT(node.HasInputWithID(ChromaKeyNode::kInvertInput));
  OLIVE_ASSERT(node.HasInputWithID(ChromaKeyNode::kMaskOnlyInput));

  OLIVE_TEST_END;
}

OLIVE_ADD_TEST(NodeFactory_InternalID) {
  NodeFactory::Initialize();

  for (int i = 0; i < NodeFactory::kInternalNodeCount; i++) {
    Node* n = NodeFactory::CreateFromFactoryIndex(static_cast<NodeFactory::InternalID>(i));
    OLIVE_ASSERT(n != nullptr);
    OLIVE_ASSERT(!n->id().isEmpty());
    delete n;
  }

  NodeFactory::Destroy();

  OLIVE_TEST_END;
}

}

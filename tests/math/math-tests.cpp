#include "testutil.h"
#include "node/math/math/mathbase.h"
#include "node/value/valuenode.h"

namespace olive {

OLIVE_ADD_TEST(MathNode_PerformAll_Int) {
  MathNodeBase node;

  OLIVE_ASSERT_EQUAL(node.PerformAll(MathNodeBase::kOpAdd, 5, 3), 8);
  OLIVE_ASSERT_EQUAL(node.PerformAll(MathNodeBase::kOpSubtract, 10, 4), 6);
  OLIVE_ASSERT_EQUAL(node.PerformAll(MathNodeBase::kOpMultiply, 6, 7), 42);
  OLIVE_ASSERT_EQUAL(node.PerformAll(MathNodeBase::kOpDivide, 15, 3), 5);
  OLIVE_ASSERT_EQUAL(node.PerformAll(MathNodeBase::kOpPower, 2, 3), 8);

  OLIVE_TEST_END;
}

OLIVE_ADD_TEST(MathNode_PerformAll_Float) {
  MathNodeBase node;

  OLIVE_ASSERT(node.PerformAll(MathNodeBase::kOpAdd, 2.5, 1.5) == 4.0);
  OLIVE_ASSERT(node.PerformAll(MathNodeBase::kOpSubtract, 10.0, 3.5) == 6.5);
  OLIVE_ASSERT(node.PerformAll(MathNodeBase::kOpMultiply, 3.0, 4.5) == 13.5);
  OLIVE_ASSERT(node.PerformAll(MathNodeBase::kOpDivide, 7.0, 2.0) == 3.5);
  OLIVE_ASSERT(node.PerformAll(MathNodeBase::kOpPower, 9.0, 0.5) == 3.0);

  OLIVE_TEST_END;
}

OLIVE_ADD_TEST(MathNode_PerformAddSub) {
  MathNodeBase node;

  OLIVE_ASSERT_EQUAL(node.PerformAddSub(MathNodeBase::kOpAdd, 100, 50), 150);
  OLIVE_ASSERT_EQUAL(node.PerformAddSub(MathNodeBase::kOpSubtract, 100, 50), 50);
  OLIVE_ASSERT_EQUAL(node.PerformAddSub(MathNodeBase::kOpMultiply, 100, 50), 100);
  OLIVE_ASSERT_EQUAL(node.PerformAddSub(MathNodeBase::kOpDivide, 100, 50), 100);
  OLIVE_ASSERT_EQUAL(node.PerformAddSub(MathNodeBase::kOpPower, 100, 50), 100);

  OLIVE_TEST_END;
}

OLIVE_ADD_TEST(MathNode_PerformMultDiv) {
  MathNodeBase node;

  OLIVE_ASSERT_EQUAL(node.PerformMultDiv(MathNodeBase::kOpAdd, 100, 50), 100);
  OLIVE_ASSERT_EQUAL(node.PerformMultDiv(MathNodeBase::kOpSubtract, 100, 50), 100);
  OLIVE_ASSERT_EQUAL(node.PerformMultDiv(MathNodeBase::kOpMultiply, 100, 50), 5000);
  OLIVE_ASSERT_EQUAL(node.PerformMultDiv(MathNodeBase::kOpDivide, 100, 50), 2);
  OLIVE_ASSERT_EQUAL(node.PerformMultDiv(MathNodeBase::kOpPower, 100, 50), 100);

  OLIVE_TEST_END;
}

OLIVE_ADD_TEST(MathNode_PerformMult) {
  MathNodeBase node;

  OLIVE_ASSERT_EQUAL(node.PerformMult(MathNodeBase::kOpAdd, 5, 3), 5);
  OLIVE_ASSERT_EQUAL(node.PerformMult(MathNodeBase::kOpSubtract, 5, 3), 5);
  OLIVE_ASSERT_EQUAL(node.PerformMult(MathNodeBase::kOpMultiply, 5, 3), 15);
  OLIVE_ASSERT_EQUAL(node.PerformMult(MathNodeBase::kOpDivide, 5, 3), 5);
  OLIVE_ASSERT_EQUAL(node.PerformMult(MathNodeBase::kOpPower, 5, 3), 5);

  OLIVE_TEST_END;
}

OLIVE_ADD_TEST(MathNode_PairingResolve) {
  using P = MathNodeBase::PairingCalculator;

  OLIVE_ASSERT_EQUAL(P::Resolve(NodeValue::kFloat, NodeValue::kFloat), MathNodeBase::kPairNumberNumber);
  OLIVE_ASSERT_EQUAL(P::Resolve(NodeValue::kFloat, NodeValue::kColor), MathNodeBase::kPairNumberColor);
  OLIVE_ASSERT_EQUAL(P::Resolve(NodeValue::kColor, NodeValue::kColor), MathNodeBase::kPairColorColor);
  OLIVE_ASSERT_EQUAL(P::Resolve(NodeValue::kTexture, NodeValue::kFloat), MathNodeBase::kPairTextureNumber);
  OLIVE_ASSERT_EQUAL(P::Resolve(NodeValue::kTexture, NodeValue::kTexture), MathNodeBase::kPairTextureTexture);
  OLIVE_ASSERT_EQUAL(P::Resolve(NodeValue::kVec2, NodeValue::kVec2), MathNodeBase::kPairVecVec);
  OLIVE_ASSERT_EQUAL(P::Resolve(NodeValue::kVec2, NodeValue::kFloat), MathNodeBase::kPairVecNumber);
  OLIVE_ASSERT_EQUAL(P::Resolve(NodeValue::kMatrix, NodeValue::kMatrix), MathNodeBase::kPairMatrixMatrix);
  OLIVE_ASSERT_EQUAL(P::Resolve(NodeValue::kMatrix, NodeValue::kVec2), MathNodeBase::kPairMatrixVec);
  OLIVE_ASSERT_EQUAL(P::Resolve(NodeValue::kSamples, NodeValue::kSamples), MathNodeBase::kPairSampleSample);
  OLIVE_ASSERT_EQUAL(P::Resolve(NodeValue::kSamples, NodeValue::kFloat), MathNodeBase::kPairSampleNumber);
  OLIVE_ASSERT_EQUAL(P::Resolve(NodeValue::kTexture, NodeValue::kColor), MathNodeBase::kPairTextureColor);
  OLIVE_ASSERT_EQUAL(P::Resolve(NodeValue::kTexture, NodeValue::kMatrix), MathNodeBase::kPairTextureMatrix);

  OLIVE_TEST_END;
}

OLIVE_ADD_TEST(MathNode_PairingResolve_None) {
  using P = MathNodeBase::PairingCalculator;

  OLIVE_ASSERT_EQUAL(P::Resolve(NodeValue::kNone, NodeValue::kFloat), MathNodeBase::kPairNone);
  OLIVE_ASSERT_EQUAL(P::Resolve(NodeValue::kFloat, NodeValue::kNone), MathNodeBase::kPairNone);
  OLIVE_ASSERT_EQUAL(P::Resolve(NodeValue::kNone, NodeValue::kNone), MathNodeBase::kPairNone);

  OLIVE_TEST_END;
}

}

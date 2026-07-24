#ifndef COLORIZENODE_H
#define COLORIZENODE_H

#include "node/node.h"

namespace olive {

class ColorizeNode : public Node
{
  Q_OBJECT
public:
  ColorizeNode();

  NODE_DEFAULT_FUNCTIONS(ColorizeNode)

  virtual QString Name() const override;
  virtual QString id() const override;
  virtual QVector<CategoryID> Category() const override;
  virtual QString Description() const override;

  virtual void Retranslate() override;

  virtual ShaderCode GetShaderCode(const ShaderRequest &request) const override;
  virtual void Value(const NodeValueRow& value, const NodeGlobals &globals, NodeValueTable *table) const override;

  static const QString kTextureInput;
  static const QString kColorInput;
  static const QString kSaturationInput;
  static const QString kStrengthInput;
  static const QString kPreserveLuminosityInput;

};

}

#endif // COLORIZENODE_H

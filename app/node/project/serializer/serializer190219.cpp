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

#include "serializer190219.h"

#include <QMessageBox>

namespace olive {

ProjectSerializer::LoadData ProjectSerializer190219::Load(Project *project, QXmlStreamReader *reader, LoadType load_type, void *reserved) const
{
  Q_UNUSED(project)
  Q_UNUSED(reader)
  Q_UNUSED(load_type)
  Q_UNUSED(reserved)

  // Olive 0.1 project format is not supported in this version.
  // The format changed significantly between 0.1 and 0.2, and the old serializer
  // was not ported forward. Users can open 0.1 projects in Olive 0.1 and
  // re-export them, or manually recreate them.
  qWarning() << "Olive 0.1 project format is not supported. Please use Olive 0.1 to upgrade your project.";

  return LoadData();
}

}

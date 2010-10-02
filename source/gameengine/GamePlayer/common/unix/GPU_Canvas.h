/**
 * $Id: GPU_Canvas.h 26841 2010-02-12 13:34:04Z campbellbarton $
 *
 * ***** BEGIN GPL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef __GPU_CANVAS_H
#define __GPU_CANVAS_H

#include <iostream>

#include "KXH_ketsji_hooks.h"
#include "GPC_Canvas.h"

class GPU_Canvas : public GPC_Canvas
{
private:
	
	/** Handle to the drawing resource. */
	KXH_plugin_handle m_plugin;
		
public:
	GPU_Canvas(KXH_plugin_handle display, int width, int height);
	virtual ~GPU_Canvas();
	
	virtual void Init(void);

	bool BeginDraw(void);
	void EndDraw(void);
	virtual void SwapBuffers(void);

};

#endif  // __GPU_CANVAS_H


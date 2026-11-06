import bpy, math, os, subprocess
from mathutils import Vector

# Koh-i-Noor — procedural 3D short
# Blender 4.2+ | FFmpeg required
QUALITY = os.environ.get("KOHINOOR_QUALITY", "PREVIEW").upper()  # PREVIEW or FINAL
FPS = 24
W, H = (1080, 1920) if QUALITY == "FINAL" else (540, 960)
SAMPLES = 48 if QUALITY == "FINAL" else 12
ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "renders")
os.makedirs(OUT, exist_ok=True)

def clear():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        pass

def mat(name, color, metallic=0.0, rough=.3, transmission=0.0, emission=0.0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    p=m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value=(*color,1)
    p.inputs["Metallic"].default_value=metallic; p.inputs["Roughness"].default_value=rough
    if "Transmission" in p.inputs: p.inputs["Transmission"].default_value=transmission
    if "IOR" in p.inputs: p.inputs["IOR"].default_value=2.417 if transmission else 1.45
    if emission:
        p.inputs["Emission Color"].default_value=(*color,1); p.inputs["Emission Strength"].default_value=emission
    return m

GOLD=mat("Antique gold",(.55,.30,.075),.82,.22)
GOLD_DARK=mat("Aged bronze",(.12,.065,.022),.78,.3)
DARK=mat("Obsidian",(.006,.009,.016),.25,.24)
STONE=mat("Sandstone",(.22,.13,.07),.12,.48)
BLUE=mat("Midnight blue",(.012,.025,.055),.35,.22)
DIAMOND=mat("Optical diamond",(.68,.86,1.0),.05,.045,.96)
WHITE=mat("White gold",(.8,.78,.68),.85,.16)

def cube(name, loc, scale, material, bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o=bpy.context.object; o.name=name
    o.dimensions=scale; bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(material)
    if bevel:
        mod=o.modifiers.new("Soft machined edges","BEVEL"); mod.width=bevel; mod.segments=3
    return o

def uv_sphere(name, loc, scale, material):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, location=loc); o=bpy.context.object
    o.name=name; o.scale=scale; o.data.materials.append(material); bpy.ops.object.shade_smooth(); return o

def cyl(name, loc, radius, depth, material, vertices=96):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc)
    o=bpy.context.object; o.name=name; o.data.materials.append(material); bevel=o.modifiers.new("Edge glints","BEVEL"); bevel.width=.025; bevel.segments=3
    return o

def text_obj(body, loc, size, material, align='CENTER'):
    cu=bpy.data.curves.new("Title","FONT"); cu.body=body; cu.size=size; cu.align_x=align; cu.extrude=.002
    ob=bpy.data.objects.new(body,cu); bpy.context.collection.objects.link(ob); ob.location=loc; ob.data.materials.append(material); return ob

def light(name, typ, loc, energy, color, size=4, target=(0,0,0)):
    data=bpy.data.lights.new(name,typ); data.energy=energy; data.color=color
    if typ=='AREA': data.shape='DISK'; data.size=size
    ob=bpy.data.objects.new(name,data); bpy.context.collection.objects.link(ob); ob.location=loc
    ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler(); return ob

def camera(loc, target=(0,0,0), lens=52):
    data=bpy.data.cameras.new("Cinema camera"); ob=bpy.data.objects.new("Cinema camera",data); bpy.context.collection.objects.link(ob)
    ob.location=loc; ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler(); data.lens=lens; bpy.context.scene.camera=ob; return ob

def diamond(loc=(0,0,0), scale=1):
    # Procedural brilliant-like faceted stone with crown, girdle and pavilion.
    verts=[]; rings=[(1.05,-.12,16),(.78,.42,16),(.48,.58,16),(.22,.63,16),(.82,-.20,16),(.55,-.72,16),(.0,-1.18,1)]
    for r,z,n in rings:
        if n==1: verts.append((0,0,z)); continue
        for i in range(n):
            a=2*math.pi*i/n + (math.pi/16 if len(verts)>0 else 0)
            verts.append((r*math.cos(a),r*math.sin(a),z))
    faces=[]; offsets=[0,16,32,48,64,80,96]
    for ri in range(6):
        n=16
        if ri==5:
            for i in range(n): faces.append((offsets[ri]+i,offsets[ri]+(i+1)%n,offsets[ri+1]))
        else:
            for i in range(n):
                a=offsets[ri]+i; b=offsets[ri]+(i+1)%n; c=offsets[ri+1]+(i+1)%n; d=offsets[ri+1]+i
                faces.extend([(a,b,c),(a,c,d)])
    mesh=bpy.data.meshes.new("Cut gemstone mesh"); mesh.from_pydata(verts,[],faces); mesh.materials.append(DIAMOND)
    ob=bpy.data.objects.new("Koh-i-Noor | faceted gemstone",mesh); bpy.context.collection.objects.link(ob); ob.location=loc; ob.scale=(scale,scale,scale)
    # Tiny bevels catch the rim light without destroying facets.
    bevel=ob.modifiers.new("Facet edge polish","BEVEL"); bevel.width=.008*scale; bevel.segments=1
    return ob

def room_mughal():
    # Grand axial hall with repeated arches, columns and gold detailing.
    cube("Marble floor",(0,0,-2.0),(15,22,.35),STONE)
    for y in (-7,-3,1,5,9):
        for x in (-5.2,5.2):
            cyl("Carved column",(x,y,0),.38,4.2,GOLD_DARK,48)
            for z in (-1.9,1.9): cyl("Column capital",(x,y,z),.58,.25,GOLD,48)
    for x in (-5.2,5.2):
        cube("Hall wall",(x,0,1.0),(.35,20,6),GOLD_DARK)
    for y in (-6,0,6):
        cube("Gold ceiling beam",(0,y,4.2),(11,.28,.28),GOLD)
    # central jewel pedestal
    cyl("Royal pedestal",(0,0,-1.35),1.35,.65,GOLD_DARK)
    cyl("Pedestal gold inlay",(0,0,-.98),1.15,.08,GOLD)
    diamond((0,0,.0),.78)
    for x in (-2.4,2.4):
        for y in (-2,2): uv_sphere("Treasure vessel",(x,y,-1.2),(.42,.42,.48),GOLD)

def scene_setup(idx):
    clear()
    sc=bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.samples=SAMPLES; sc.cycles.use_denoising=False
    sc.render.resolution_x=W; sc.render.resolution_y=H; sc.render.resolution_percentage=100
    sc.render.fps=FPS; sc.frame_start=1; sc.frame_end=6*FPS
    sc.render.image_settings.file_format='PNG'; sc.render.film_transparent=False
    sc.world.color=(.004,.004,.006)
    sc.view_settings.view_transform='AgX'
    # Portrait camera and atmospheric lights
    if idx==0:
        cube("Black stage",(0,0,-2.5),(30,30,.2),DARK)
        jewel=diamond((0,0,0),1.55); jewel.rotation_euler[2]=-.12
        cam=camera((0,-10,1.2),(0,0,0),55)
        light("Warm key",'AREA',(-4,-4,5),950,(1,.72,.38),5)
        light("Cool rim",'AREA',(4,1,2),1300,(.48,.68,1),3)
        light("Top glint",'AREA',(0,2,5),1600,(1,.88,.65),2)
        jewel.keyframe_insert(data_path="rotation_euler",frame=1); jewel.rotation_euler[2]+=math.radians(18); jewel.keyframe_insert(data_path="rotation_euler",frame=6*FPS)
        cam.location=(0,-11,1.8); cam.keyframe_insert(data_path="location",frame=1); cam.location=(0,-8.7,.7); cam.keyframe_insert(data_path="location",frame=6*FPS)
    elif idx==1:
        room_mughal(); cam=camera((0,-13,1.2),(0,0,.3),43)
        light("Golden hall key",'AREA',(-3,-2,7),2200,(1,.68,.32),7)
        light("Blue fill",'AREA',(4,3,3),900,(.42,.56,1),5)
        cam.location=(0,-15,1.4); cam.keyframe_insert(data_path="location",frame=1); cam.location=(0,-10,1.0); cam.keyframe_insert(data_path="location",frame=6*FPS)
    elif idx==2:
        cube("Delhi palace courtyard",(0,0,-2),(18,18,.4),STONE)
        # Palace facade and monumental entry
        cube("Palace facade",(0,3,1.5),(12,.6,7),GOLD_DARK)
        for x in (-4,-2,0,2,4):
            cube("Recessed arch",(x,2.65,1.3),(1.25,.12,4.5),STONE)
            cube("Arch dark inset",(x,2.55,1.25),(.8,.08,3.8),DARK)
        for x in (-3.5,3.5):
            cyl("Royal standard pole",(x,-1,2),.045,5,GOLD)
            # banner
            cube("Crimson standard",(x,-1,3.5),(.9,.05,1.25),mat("Crimson silk",(.28,.018,.025),.1,.5))
        # stylized distant mounted procession silhouettes
        for i in range(5):
            x=-4+i*2
            uv_sphere("Horse silhouette",(x,0,-.6),(.72,.25,.48),DARK)
            uv_sphere("Rider silhouette",(x,-.02,.25),(.22,.22,.55),GOLD_DARK)
        cam=camera((0,-15,2.1),(0,1,.2),43)
        light("Sunset shaft",'AREA',(-4,-1,7),2600,(1,.48,.2),6)
        light("Dusty fill",'AREA',(5,-4,3),750,(1,.78,.5),5)
        cam.location=(0,-17,2.3); cam.keyframe_insert(data_path="location",frame=1); cam.location=(0,-11,1.8); cam.keyframe_insert(data_path="location",frame=6*FPS)
        text_obj("DELHI • 1739",(0,-.5,4.2),.42,GOLD)
    elif idx==3:
        # Crown-inspired jeweled display: not an exact replica; use reference model for fidelity.
        cyl("Velvet display plinth",(0,0,-1.65),2.0,.55,GOLD_DARK)
        cyl("Gold crown base",(0,0,-1.25),1.55,.22,WHITE)
        # Crown circlet
        bpy.ops.mesh.primitive_torus_add(major_radius=1.28,minor_radius=.10,major_segments=96,minor_segments=16,location=(0,0,-.85))
        bpy.context.object.data.materials.append(WHITE)
        for i in range(12):
            a=2*math.pi*i/12
            x,y=1.25*math.cos(a),1.25*math.sin(a)
            uv_sphere("Crown jewel",(x,y,-.52),(.16,.16,.2),DIAMOND)
            # gold ribs rise to a central arch
            rib=cube("Crown rib",(x*.72,y*.72,.0),(.09,.09,2.1),GOLD,.035); rib.rotation_euler[1]=.35*math.cos(a); rib.rotation_euler[0]=.35*math.sin(a)
        central=diamond((0,-.1,.2),.8)
        cam=camera((0,-10,1.0),(0,0,-.1),52)
        light("Royal softbox",'AREA',(-3,-4,5),1600,(1,.82,.56),4)
        light("Crown rim",'AREA',(4,2,2),1900,(.55,.7,1),3)
        cam.location=(0,-11,1.2); cam.keyframe_insert(data_path="location",frame=1); cam.location=(0,-8.5,.65); cam.keyframe_insert(data_path="location",frame=6*FPS)
    else:
        cube("Infinite black stage",(0,0,-2),(30,30,.2),DARK)
        jewel=diamond((0,0,0),1.65)
        cam=camera((0,-10,.8),(0,0,0),55)
        light("Final gold key",'AREA',(-4,-3,5),1700,(1,.68,.28),4)
        light("White rim",'AREA',(4,1,2),1400,(.8,.9,1),2)
        jewel.rotation_euler[2]=-.2; jewel.keyframe_insert(data_path="rotation_euler",frame=1)
        jewel.rotation_euler[2]=.18; jewel.keyframe_insert(data_path="rotation_euler",frame=6*FPS)
        cam.location=(0,-11,1.2); cam.keyframe_insert(data_path="location",frame=1); cam.location=(0,-8.5,.7); cam.keyframe_insert(data_path="location",frame=6*FPS)
        text_obj("THE KOH-I-NOOR",(0,-.05,-2.15),.52,GOLD)
        text_obj("THE MOUNTAIN OF LIGHT",(0,-.05,-2.65),.22,WHITE)
    # Animate interpolation smoothly
    for ob in sc.objects:
        if ob.animation_data and ob.animation_data.action:
            for fc in ob.animation_data.action.fcurves:
                for kp in fc.keyframe_points: kp.interpolation='BEZIER'
    sc.render.image_settings.color_mode='RGB'
    sc.render.image_settings.file_format='PNG'
    return sc

def render_segment(idx):
    sc=scene_setup(idx)
    folder=os.path.join(OUT,f"scene_{idx+1}"); os.makedirs(folder,exist_ok=True)
    sc.render.filepath=os.path.join(folder,"frame_")
    bpy.ops.render.render(animation=True)
    pattern=os.path.join(folder,"frame_%04d.png")
    mp4=os.path.join(OUT,f"scene_{idx+1}.mp4")
    subprocess.run(["ffmpeg","-y","-framerate",str(FPS),"-i",pattern,"-c:v","libx264","-pix_fmt","yuv420p","-crf","17" if QUALITY=="FINAL" else "22","-r",str(FPS),mp4],check=True)
    return mp4

def main():
    clips=[render_segment(i) for i in range(5)]
    concat=os.path.join(OUT,"concat.txt")
    with open(concat,"w") as f:
        for p in clips: f.write("file '"+p.replace("'","'\\''")+"'\n")
    final=os.path.join(ROOT,"kohinoor_30s.mp4")
    subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",concat,"-c","copy","-movflags","+faststart",final],check=True)
    print("FINAL VIDEO:",final)

if __name__=="__main__": main()

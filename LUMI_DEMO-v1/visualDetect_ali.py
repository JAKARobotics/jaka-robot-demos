import time
import cv2
from OrbbecSDK.orbbecCamera import Camera
from utilfs.jaka import *
from utilfs.tools import loadJsonFile, saveOriginImg, generatorNearPoints, pixel_to_world,vl_ali


step_flag = None # -1：catch 1：put
IO_TOOL = 1 # Grab IO
PI=3.1415926

def kine_caculate(ref_pos,base_loc,world_loc,mapJsonData,step_type):   
    base2objup_pos=None
    objup2obj_pos =None
    grasp_flag =None 
    mv_type = -1 

    grip_loc = tuple(world_loc.tolist() + list(base_loc[3:]))  # A
    # obj cartesian_pose
    grip_loc = list(grip_loc)
    grip_loc[0] += mapJsonData["robotParams"]["RelativeOffset-X"]
    grip_loc[1] += mapJsonData["robotParams"]["RelativeOffset-Y"]

    if step_type == -1:
        # catch
        grip_loc[2] += mapJsonData["robotParams"]["RelativeOffset-Z"]

    elif step_type == 1:
        # put
        grip_loc[2] += mapJsonData["robotParams"]["RelativeOffset-Zput"]

    # obj-up cartesian_pose
    grip_loc_up = grip_loc[:]
    grip_loc_up[2] = grip_loc_up[2] + mapJsonData["robotParams"]["relativeUpMotionHeight"]
    
    grip_loc = tuple(grip_loc)
    grip_loc_up = tuple(grip_loc_up)  

    # base 2 obj 
    base2obj_pos = robot.kine_inverse_origin(ref_pos, grip_loc)
    # base 2 obj-up
    base2objup_pos = robot.kine_inverse_origin(ref_pos, grip_loc_up)
   
    # if base2obj-up faluire, turn to base2a
    if base2objup_pos[0]!=0:
        grasp_flag= base2obj_pos[0]
        mv_type = 1
    
    # if base2obj-up success, turn to obj-up2obj
    elif  base2objup_pos[0]==0:
        objup2obj_pos = robot.kine_inverse_origin(base2objup_pos[1], grip_loc)
        if objup2obj_pos[0]==0:
            grasp_flag= objup2obj_pos[0]
            mv_type = 2
        else:
            grasp_flag = base2obj_pos[0] 
            mv_type = 1
    return mv_type,grip_loc,grip_loc_up,base2obj_pos,base2objup_pos,objup2obj_pos,grasp_flag 


def jointMove(mv_type,base2obj_pos,base2objup_pos,objup2obj_pos,grab_status):
    # base move 2 obj-up 2 obj 
    if mv_type == 2: # base move 2 obj-up
        ret_base2objup = robot.joint_move_origin(base2objup_pos[1], 1, 0)
        if ret_base2objup == 0:
            time.sleep(1)
            ret_move2obj = robot.joint_move_origin(objup2obj_pos[1], 1, 0)
            if ret_move2obj == 0:
                robot.grab_action(grab_status)
                time.sleep(3)
                moveRet = robot.joint_move_origin(base2objup_pos[1], 1, 0)
                if moveRet == 0:
                    print("obj move 2 obj-up success")
                else:
                    print("obj move 2 obj-up failure")
                time.sleep(1)

            else:
                print("obj-up move 2 obj failure")    
        else:
            print("base move 2 obj-up failure")   
    # base 2 obj
    if mv_type == 1:
        ret_move2obj = robot.joint_move_origin(base2obj_pos[1], 1, 0)
        if ret_move2obj == 0:
            time.sleep(1)
            robot.grab_action(grab_status)
            time.sleep(3)
            print('next: obj move 2 put-up')
        else:
            print("base move 2 obj failure")
    return 

if __name__=='__main__':
    mapJsonData = loadJsonFile('./conf/userCmdControl.json')
    calibParams = loadJsonFile('./conf/CalibParams.json')

    robot = JAKA(mapJsonData["calibrateParams"]["robotIP"], connect=True)
    robot._login()

    # robot move to basepose
    base_loc = mapJsonData["robotParams"]["basePose"] 
    robot.joint_move_origin(base_loc, 1, 0)
   
    # open grab
    robot.grab_action(0)
    time.sleep(2)

    mv_obj = mapJsonData["objects"]["moveObjects"]
    put_obj = mapJsonData["objects"]["putObject"]
    tags=[mv_obj,put_obj]

    detect_continue = True # Repeated detection and grabbing

    while detect_continue:
        mv_objs = []  # Allow multiple similar items
        put_objs = []  # Only one target location.
        mv_centers, put_center = [],[]

        # Get image
        cam = Camera()
        color_img, depth_data, _ = cam.getColorDepthData()
        cam.close()

        # Save  originimg
        img_path = saveOriginImg(color_img,mapJsonData["cameraParams"]["saveImgPath"])

        # Objects Detection
        obj_labels,obj_locs = vl_ali(tags, img_path)
        cam.close()

        if len(obj_labels) != len(obj_locs):
            if put_obj not in obj_labels:
                black_name = len(obj_locs) - len(obj_labels)
                for i in range(black_name - 1):
                    obj_labels.append(obj_labels[0])
                obj_labels.append(put_obj)
            else:
                obj_labels = [mv_obj for _ in range(len(obj_locs) - 1)]
                obj_labels.append(put_obj)

        for i in range(len(obj_labels)):
            # print('objPos:',objPos)
            center_x = (int(obj_locs[i][0]) + int(obj_locs[i][2])) / 2
            center_y = (int(obj_locs[i][1]) + int(obj_locs[i][3])) / 2
            if obj_labels[i]==mv_obj:
                mv_objs.append(obj_locs[i])
                mv_centers.append([int(center_x), int(center_y)])
            if obj_labels[i]==put_obj:
                put_objs.append(obj_locs[i])
                put_center.append([int(center_x), int(center_y)])
        print("mv_objs,mv_centers: ",mv_objs,mv_centers)
        print("put_objs,put_center: ",put_objs,put_center)


        for i in range(len(mv_objs)):
            cur_obj_pos = mv_objs[i]
            cur_center_pos = mv_centers[i]
            cv2.rectangle(color_img, (cur_obj_pos[0], cur_obj_pos[1]),
                            (cur_obj_pos[2], cur_obj_pos[3]), (0, 0, 255), 2)

            mv_obj_depth = depth_data[cur_center_pos[1], cur_center_pos[0]]

            # Current point gets depth of 0, search for the depth of the surrounding point
            if int(mv_obj_depth) == 0:
                gen_center_points = generatorNearPoints(put_center,
                                                        mapJsonData["genNearPointParams"][
                                                            "nearPointInterval"],
                                                        mapJsonData["genNearPointParams"][
                                                            "nearPointTimes"])

                for i, point in enumerate(gen_center_points):
                    mv_obj_depth = depth_data[point[0][1], point[0][0]]
                    if int(mv_obj_depth) != 0 or i == len(gen_center_points):
                        break
            print("【{} depth is: {} (mm)】".format(mv_obj,mv_obj_depth))
            obj_world_loc = pixel_to_world(cur_center_pos, mv_obj_depth, calibParams["CameraMatrix"],
                calibParams["RotationMat"],
                calibParams["TranslationMat"])
            
            ref_pos = robot.getjoints()
            base_loc= robot.get_tcp_pos()

            print('Calculate whether the position of the item to be captured is reachable')
            mv_type,grip_loc,grip_up_loc,base2obj_pos,base2objup_pos,objup2obj_pos,grasp_flag = kine_caculate(ref_pos,base_loc,obj_world_loc,mapJsonData,step_type=-1)    

        # Put location
        put_obj_depth = depth_data[put_center[0][1], put_center[0][0]] 
        put_obj_pos = put_objs[0]  
        put_center = put_center[0]  
        cv2.rectangle(color_img, (put_obj_pos[0], put_obj_pos[1]),
                        (put_obj_pos[2], put_obj_pos[3]), (0, 0, 255), 2) 
     
        if int(put_obj_depth) == 0:
            gen_center_points=generatorNearPoints(put_center,mapJsonData["genNearPointParams"]["nearPointInterval"],mapJsonData["genNearPointParams"]["nearPointTimes"])

            for i,point in enumerate(gen_center_points):
                put_obj_depth = depth_data[point[0][1], point[0][0]]
                if int(put_obj_depth) != 0 or i==len(gen_center_points):
                    break
        print("【{} depth is: {} (mm)】".format(put_obj,put_obj_depth))
        put_world_loc = pixel_to_world(put_center, put_obj_depth, calibParams["CameraMatrix"],
                calibParams["RotationMat"],
                calibParams["TranslationMat"])

        print('Calculate whether the location of the item to be placed is reachable')
        if mv_type == 2:
            ref_pos_d = base2objup_pos[1]
        elif mv_type == 1:
            ref_pos_d = base2obj_pos[1]
        put_type,put_loc,put_loc_up,objup2put_pos,objup2putup_pos,putup2put_pos,put_flag = kine_caculate(ref_pos_d,grip_up_loc,put_world_loc,mapJsonData,step_type=1)

        cv2.imwrite(img_path,color_img)

        print('---Start Capture--')
        jointMove(mv_type,base2obj_pos,base2objup_pos,objup2obj_pos,grab_status=1)
   
        print('---Start Place---')
        jointMove(mv_type,objup2put_pos,objup2putup_pos,putup2put_pos,grab_status=0)
   

        # Move to basepose
        robot.joint_move_origin(base_loc,1,0)
        robot.grab_action(0)


        

 
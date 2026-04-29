"""
在此目录已有大量计算输入文件(.com以及.gjf)之后，自动根据文件名创建linux平台批量计算脚本，并根据指定的划分大小创建多个子任务脚本
"""

import os
import shutil
from natsort import ns, natsorted #实现自然排序的库

ORCA_ORDER = '/data/home/zlgroup/ORCA/orca_6_0_0_shared_openmpi416_avx2/orca'  # ORCA计算命令，基本需要写其完整路径
# ORCA_ORDER = '/home/user/Documents/software/orca600/orca'
def create_hpc_oder(input_dir, work_dir, num_job, job_name, node_name, core_num):
    """
    根据文件名创建linux超算平台批量计算脚本，并根据指定的划分大小创建多个子任务脚本
    :param input_dir: 输入文件所在文件夹
    :param work_dir: 超算平台工作文件夹
    :param num_job: 划分的批量计算子任务数
    """

    os.chdir(input_dir)
    irc_com_names = [f for f in os.listdir(os.getcwd()) if f.endswith(('.gjf', '.com', '.inp'))] # 得到文件夹下的所有输入文件名称
    names = natsorted(irc_com_names,alg=ns.PATH) # 实现自然排序

    text = []
    for i in names:
        filename = os.path.splitext(i)[0]
        if i.endswith(('.gjf', '.com')):
            onemol = f'g16 {i} {filename}.log\n'
        else:
            onemol = ORCA_ORDER + f' {i} > {filename}.out\n'
        text.append(onemol)

    k = 0
    writein = []
    num_work_1job = int(len(text)/num_job) # 每1个任务中对应的计算任务个数（整除数）
    for j in range(len(text)):
        if j%num_work_1job == 0 and j != 0:
            writein.append(text[k:j])
            k = j
        if j == len(text) - 1:
            writein.append(text[k:j+1])
    print('number of all calculation jobs: ' + str(len(writein)))

    # 超算命令模板
    for k in range(1,len(writein)+1):
        name = job_name + '_' + str(k)
        title = f'''#!/bin/bash
#SBATCH -J {name}
#SBATCH -p {node_name}
#SBATCH -N 1
#SBATCH -n {core_num}
#SBATCH -o %j.o
#SBATCH -e %j.e
#SBATCH --mail-type=ALL # 发送哪一种email通知：BEGIN,END,FAIL,ALL
#SBATCH --mail-user=tangkunmail@163.com''' + f'\n\ncd {work_dir}\n'''
# SBATCH -t 10-0:00 # 运行总时间，天数-小时数-分钟， D-HH:MM

        with open(input_dir + '/' + name + '.sh', mode = 'w', newline='') as fs: #newline=''就可以自动保存为Unix格式的文件，便于Linux系统识别
            string = [title] + writein[k-1]
            fs.writelines(string)
            

def create_local_order(input_dir, num_job, job_name):
    """
    根据文件名创建本地计算脚本，并根据指定的划分大小创建多个子任务脚本
    :param input_dir: 输入文件所在文件夹
    :param num_job: 划分的批量计算子任务数
    :param job_name: 任务名称
    """

    os.chdir(input_dir)
    irc_com_names = [f for f in os.listdir(os.getcwd()) if f.endswith(('.gjf', '.com', '.inp'))]
    names = natsorted(irc_com_names, alg=ns.PATH)

    text = []
    for i in names:
        if i.endswith('.gjf'):
            onemol = 'g16 ' + i + ' ' + i.split('.')[0] + '.log\n'
            text.append(onemol)
        elif i.endswith('.com'):
            onemol = 'g16 ' + i + ' ' + i.split('.')[0] + '.log\n'
            text.append(onemol)
        elif i.endswith('.inp'):
            onemol = f'{ORCA_ORDER} {i} > {i.split(".")[0]}.out\n'
            text.append(onemol)

    k = 0
    writein = []
    num_work_1job = int(len(text) // num_job) # 每1个任务中对应的计算任务个数（整除数）
    remainder = len(text) % num_job # 计算余数
    for j in range(len(text)):
        if j % num_work_1job == 0 and j != 0:
            writein.append(text[k:j])
            k = j
        if j == len(text) - 1:
            if remainder == 0:
                writein.append(text[k:j+1])
            else:
                writein[-1] += ''.join(text[k:j+1])
    print('number of all calculation jobs: ' + str(len(writein)))

    # 本地命令模板
    for k in range(1,len(writein)+1):
        name = job_name + '_' + str(k)
        title = f'''#!/bin/bash\n'''

        with open(input_dir + '/' + name + '.sh', mode = 'w', newline='') as fs: #newline=''就可以自动保存为Unix格式的文件，便于Linux系统识别
            string = [title] + writein[k-1]
            fs.writelines(string)

def create_xtb_folders(input_orders_dir):
    """
    将创建的xTB计算脚本分别移动到对应文件夹中，以方便批量计算
    注意：先要用create_local_order创建好计算的sh脚本，然后此函数根据计算脚本将对应文件移动到单独文件夹中
    :param input_orders_dir: 输入文件以及计算指令所在文件夹
    """

    os.chdir(input_orders_dir)
    sh_name = [x for x in os.listdir(input_orders_dir) if x.endswith('.sh')]
    sh_name.remove('xtb.sh')
    for s in sh_name:
        job_id_gjf = []
        with open(s, 'r') as fs:
            strings = fs.readlines()
        for line in strings:
            if 'g16' in line:
                job_id_gjf.append(line.split(' ')[1])
        new_folder = s.split('.')[0]# + '_freq'
        if not os.path.exists(new_folder):
            # 文件夹不存在，因此创建文件夹
            os.makedirs(new_folder)
        shutil.copy(s, new_folder)
        shutil.copy('./xtb.sh', new_folder)
        shutil.copy('./extderi', new_folder)
        shutil.copy('./extderi.f90', new_folder)
        shutil.copy('./genxyz', new_folder)
        shutil.copy('./genxyz.f90', new_folder)
        for n in job_id_gjf:
            shutil.copy(n, new_folder)

if __name__ == '__main__':

    input_dir = r"/mnt/d/CProLab/MBH_rmlp/datasets/mlip_datagen/energy/31_inp"

    num_job = 31
    job_name = 'job'

    # node_name = 'kshcnormal'
    # core_num = 32  # 曙光
    # work_dir = '/public/home/scnabhbolv/tangkun/MBH_energy/CPU-2'  # 曙光

    core_num = 28  # 东方(需要conda deactivate后才能算ORCA)
    node_name = 'normal1'
    work_dir = '/data/home/zlgroup/tangkun/MBH_energy/31inp'  # 东方
    """
    东方超算计算之前的准备：
    # 1. 避免 conda 污染
    conda deactivate

    # 2. 加 MPI（如果有 module）
    module load openmpi/4.1.6
    """

    create_hpc_oder(input_dir, work_dir, num_job, job_name, node_name, core_num)
    # create_local_order(input_dir, num_job, job_name)
    # create_xtb_folders(input_dir)  # 将创建的xTB计算脚本分别移动到对应文件夹中，以方便批量计算,注意：先要用create_local_order创建好计算的sh脚本




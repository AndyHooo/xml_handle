# _*_ coding: utf-8 _*_
'''
Created on 2018年2月1日
定时任务xml文件转换为集群版
@author: hudaqiang
'''
import os
import glob
import xml_util

py_path=os.path.abspath('.')
source_file_parent_path = py_path + '/source'
converted_file_parent_path = py_path + '/converted'
proxy_class = 'com.andy.quartz.JobDetailBean'
data_source_str = 'dataSource'
quartz_properties_path = 'quartz.properties'
job_factory_class = 'com.andy.quartz.AutoWiringSpringBeanJobFactory'

def convert():
    print '开始转换...'
    xml_files = load_xml_files()
    for xml_file in xml_files:
        file_name = xml_file.split(os.path.sep)[-1]
        converted_file_path = converted_file_parent_path + "/" + file_name
        
        tree = xml_util.read_xml(xml_file) 
        root = tree.getroot()
        
        """
        修改非task标签编写的定时任务
        """
        bean_nodes = xml_util.find_nodes(root, '{http://www.springframework.org/schema/beans}bean')
        
        #修改org.springframework.scheduling.quartz.CronTriggerBean
        CronTriggerBean_nodes = xml_util.get_node_by_keyvalue(bean_nodes, {"class":"org.springframework.scheduling.quartz.CronTriggerBean"})
        xml_util.change_node_properties(CronTriggerBean_nodes, {"class": "org.springframework.scheduling.quartz.CronTriggerFactoryBean"})
              
        #修改org.springframework.scheduling.quartz.MethodInvokingJobDetailFactoryBean
        CronTriggerBean_property_nodes = xml_util.get_childrens(CronTriggerBean_nodes)
        jobDetail_nodes = xml_util.get_node_by_keyvalue(CronTriggerBean_property_nodes, {"name":"jobDetail"})
        jobDetail_child_nodes = xml_util.get_childrens(jobDetail_nodes)
        MethodInvokingJobDetailFactoryBean_nodes = xml_util.get_node_by_keyvalue(jobDetail_child_nodes, {"class":"org.springframework.scheduling.quartz.MethodInvokingJobDetailFactoryBean"})              
        xml_util.change_node_properties(MethodInvokingJobDetailFactoryBean_nodes, {"class": "org.springframework.scheduling.quartz.JobDetailFactoryBean"})
        
        #org.springframework.scheduling.quartz.JobDetailFactoryBean添加新的属性
        durability_node = xml_util.create_node("property", {"name":"durability","value":"true"},'')
        requestsRecovery_node = xml_util.create_node("property", {"name":"requestsRecovery","value":"true"},'')
        jobClass_node = xml_util.create_node("property", {"name":"jobClass","value":proxy_class},'')
        jmisfireInstruction_node = xml_util.create_node("property", {"name":"misfireInstruction" ,"value":"2"},'')
        
        xml_util.add_child_nodes(MethodInvokingJobDetailFactoryBean_nodes, durability_node)
        xml_util.add_child_nodes(MethodInvokingJobDetailFactoryBean_nodes, requestsRecovery_node)
        xml_util.add_child_nodes(MethodInvokingJobDetailFactoryBean_nodes, jobClass_node)
        xml_util.add_child_nodes(CronTriggerBean_nodes, jmisfireInstruction_node)
        
        
        #<property name="targetObject" ref="ashareFollowBankerTask" />
        #<property name="targetMethod" value="updateAshareFollowBankerTask" />
        #<property name="concurrent" value="false" />
        #改成
        #<property name="jobDataAsMap">
        #    <map>
        #        <entry key="targetObject" value="demoTask" />
        #        <entry key="targetMethod" value="task3" />
        #    </map>
        #</property>
        
        for node in MethodInvokingJobDetailFactoryBean_nodes:
            
            property_nodes = xml_util.get_children(node)
            targetObject_node = xml_util.get_node_by_keyvalue(property_nodes, {"name":"targetObject"})[0]
            targetMethod_node = xml_util.get_node_by_keyvalue(property_nodes, {"name":"targetMethod"})[0]  
            concurrent_node = xml_util.get_node_by_keyvalue(property_nodes, {"name":"concurrent"})[0]
                     
            targetObject = xml_util.get_attrib(targetObject_node, 'ref')
            targetMethod = xml_util.get_attrib(targetMethod_node, 'value')
            
            node.remove(targetObject_node)        
            node.remove(targetMethod_node) 
            node.remove(concurrent_node)
            
            targetObject_entry_node = xml_util.create_node("entry",{"key":"targetObject","value":targetObject},'')
            targetMethod_entry_node = xml_util.create_node("entry",{"key":"targetMethod","value":targetMethod},'')
            map_node = xml_util.create_node('map',{},'')
            
            xml_util.add_child_node(map_node, targetObject_entry_node)
            xml_util.add_child_node(map_node, targetMethod_entry_node)
            
            jobDataAsMap_node = xml_util.create_node("property", {"name":"jobDataAsMap"},'')
            xml_util.add_child_node(jobDataAsMap_node, map_node)
            
            xml_util.add_child_node(node, jobDataAsMap_node)
            
        #修改org.springframework.scheduling.quartz.SchedulerFactoryBean
        #<property name="dataSource" ref="dataSource" />
        #<property name="overwriteExistingJobs" value="true" />
        #<!--注册到调度器仓库中-->
        #<property name="exposeSchedulerInRepository" value="true" />
        #<!-- 设置自动启动 -->
        #<property name="autoStartup" value="true" />
        #<property name="startupDelay" value="10" />
        #<property name="applicationContextSchedulerContextKey" value="applicationContextKey" />
        #<property name="configLocation" value="classpath:quartz.properties" />
        #<property name="jobFactory">
        #    <bean class="com.andy.quartz.AutoWiringSpringBeanJobFactory" />
        #</property>
        SchedulerFactoryBean_nodes = xml_util.get_node_by_keyvalue(bean_nodes, {"class":"org.springframework.scheduling.quartz.SchedulerFactoryBean"})   
        dataSource_node = xml_util.create_node("property",{"name":"dataSource","ref":data_source_str},'')
        overwriteExistingJobs_node = xml_util.create_node("property",{"name":"overwriteExistingJobs","value":"true"},'')
        exposeSchedulerInRepository_node = xml_util.create_node("property",{"name":"exposeSchedulerInRepository","value":"true"},'')
        autoStartup_node = xml_util.create_node("property",{"name":"autoStartup","value":"true"},'')
        startupDelay_node = xml_util.create_node("property",{"name":"startupDelay","value":"10"},'')
        applicationContextSchedulerContextKey_node = xml_util.create_node("property",{"name":"applicationContextSchedulerContextKey","value":"applicationContextKey"},'')
        configLocation_node = xml_util.create_node("property",{"name":"configLocation","value":quartz_properties_path},'')
        jobFactory_node = xml_util.create_node("property",{"name":"jobFactory"},'')
        AutoWiringSpringBeanJobFactory_node = xml_util.create_node("bean",{"class":"com.andy.quartz.AutoWiringSpringBeanJobFactory"},'')
        
        xml_util.add_child_node(jobFactory_node,AutoWiringSpringBeanJobFactory_node)
        xml_util.add_child_nodes(SchedulerFactoryBean_nodes, dataSource_node)
        xml_util.add_child_nodes(SchedulerFactoryBean_nodes, overwriteExistingJobs_node)
        xml_util.add_child_nodes(SchedulerFactoryBean_nodes, exposeSchedulerInRepository_node)
        xml_util.add_child_nodes(SchedulerFactoryBean_nodes, autoStartup_node)
        xml_util.add_child_nodes(SchedulerFactoryBean_nodes, startupDelay_node)
        xml_util.add_child_nodes(SchedulerFactoryBean_nodes, applicationContextSchedulerContextKey_node)
        xml_util.add_child_nodes(SchedulerFactoryBean_nodes, configLocation_node)
        xml_util.add_child_nodes(SchedulerFactoryBean_nodes, jobFactory_node)
        
        
        """
        修改task标签编写的定时任务
        """
        #删除scheduler节点
        scheduler_nodes = xml_util.find_nodes(root, '{http://www.springframework.org/schema/task}scheduler')
        xml_util.del_nodes(root, scheduler_nodes)
        
        scheduled_tasks_nodes = xml_util.find_nodes(root, '{http://www.springframework.org/schema/task}scheduled-tasks')
        scheduled_nodes = xml_util.get_childrens(scheduled_tasks_nodes)
        
        #创建SchedulerFactoryBean,如果存在就不需要创建
        bean_nodes = xml_util.find_nodes(root, '{http://www.springframework.org/schema/beans}bean')
        SchedulerFactoryBean_nodes = xml_util.get_node_by_keyvalue(bean_nodes, {"class":"org.springframework.scheduling.quartz.SchedulerFactoryBean"})
        if SchedulerFactoryBean_nodes == None or len(SchedulerFactoryBean_nodes) == 0:
            SchedulerFactoryBean_node = xml_util.create_node('bean',{'class':'org.springframework.scheduling.quartz.SchedulerFactoryBean'},'')
        else:
            SchedulerFactoryBean_node = SchedulerFactoryBean_nodes[0]
            
        triggers_node = xml_util.create_node('property',{'name':'triggers'},'')
        list_node = xml_util.create_node('list',{},'')
        
        for node in scheduled_nodes:
            targetObject = xml_util.get_attrib(node, 'ref')
            targetMethod = xml_util.get_attrib(node, 'method')
            try:
                cron = xml_util.get_attrib(node, 'cron')
            except:
                fixed_delay = xml_util.get_attrib(node,'fixed-delay')
                cron = '0/' + str(int(fixed_delay) / 1000) + ' * * * * ?'
            
            #删除当前scheduled节点
            xml_util.del_node(scheduled_tasks_nodes[0], node)
            
            #创建CronTriggerFactoryBean节点
            CronTriggerFactoryBean_id = targetMethod + 'Trigger'
            CronTriggerFactoryBean_node = xml_util.create_node('bean',{'id':CronTriggerFactoryBean_id,'class':'org.springframework.scheduling.quartz.CronTriggerFactoryBean'},'')
            
            #创建创建CronTriggerFactoryBean的属性子节点
            cronExpression_node = xml_util.create_node('property',{'name':'cronExpression','value':cron},'')
            
            #创建misfireInstruction节点
            misfireInstruction_node = xml_util.create_node('property',{'name':'misfireInstruction','value':'2'},'')
            
            #创建jobDetail节点
            jobDetail_node = xml_util.create_node('property',{'name':'jobDetail'},'')
            
            #创建JobDetailFactoryBean节点
            JobDetailFactoryBean_node = xml_util.create_node('bean', {'class':'org.springframework.scheduling.quartz.JobDetailFactoryBean'}, '')
            
            #创建JobDetailFactoryBean的属性子节点
            durability_node = xml_util.create_node('property',{'name':'durability','value':'true'},'')
            requestsRecovery_node = xml_util.create_node('property',{'name':'requestsRecovery','value':'false'},'')
            jobClass_node = xml_util.create_node('property',{'name':'jobClass','value':proxy_class},'')
            jobDataAsMap_node = xml_util.create_node('property',{'name':'jobDataAsMap'},'')
            
            map_node = xml_util.create_node('map',{},'')
            targetObject_node = xml_util.create_node('entry',{'key':'targetObject','value':targetObject},'')
            targetMethod_node = xml_util.create_node('entry',{'key':'targetMethod','value':targetMethod},'')
            
            xml_util.add_child_node(map_node,targetObject_node)
            xml_util.add_child_node(map_node,targetMethod_node)
            xml_util.add_child_node(jobDataAsMap_node,map_node)
            
            xml_util.add_child_node(JobDetailFactoryBean_node,durability_node)
            xml_util.add_child_node(JobDetailFactoryBean_node,requestsRecovery_node)
            xml_util.add_child_node(JobDetailFactoryBean_node,jobClass_node)
            xml_util.add_child_node(JobDetailFactoryBean_node,jobDataAsMap_node)
            
            xml_util.add_child_node(jobDetail_node,JobDetailFactoryBean_node)
            
            xml_util.add_child_node(CronTriggerFactoryBean_node,jobDetail_node)
            xml_util.add_child_node(CronTriggerFactoryBean_node,cronExpression_node)
            xml_util.add_child_node(CronTriggerFactoryBean_node,misfireInstruction_node)
            
            xml_util.add_child_node(root,CronTriggerFactoryBean_node)
            ref_node = xml_util.create_node('ref',{'bean':CronTriggerFactoryBean_id},'')
            xml_util.add_child_node(list_node,ref_node)
           
        xml_util.del_nodes(root,scheduled_tasks_nodes)
        xml_util.add_child_node(triggers_node,list_node)
        #创建SchedulerFactoryBean
        dataSource_node = xml_util.create_node("property",{"name":"dataSource","ref":data_source_str},'')
        overwriteExistingJobs_node = xml_util.create_node("property",{"name":"overwriteExistingJobs","value":"true"},'')
        exposeSchedulerInRepository_node = xml_util.create_node("property",{"name":"exposeSchedulerInRepository","value":"true"},'')
        autoStartup_node = xml_util.create_node("property",{"name":"autoStartup","value":"true"},'')
        startupDelay_node = xml_util.create_node("property",{"name":"startupDelay","value":"10"},'')
        applicationContextSchedulerContextKey_node = xml_util.create_node("property",{"name":"applicationContextSchedulerContextKey","value":"applicationContextKey"},'')
        configLocation_node = xml_util.create_node("property",{"name":"configLocation","value":quartz_properties_path},'')
        jobFactory_node = xml_util.create_node("property",{"name":"jobFactory"},'')
        AutoWiringSpringBeanJobFactory_node = xml_util.create_node("bean",{"class":"com.andy.quartz.AutoWiringSpringBeanJobFactory"},'')
        
        xml_util.add_child_node(jobFactory_node,AutoWiringSpringBeanJobFactory_node)
        xml_util.add_child_node(SchedulerFactoryBean_node, dataSource_node)
        xml_util.add_child_node(SchedulerFactoryBean_node, overwriteExistingJobs_node)
        xml_util.add_child_node(SchedulerFactoryBean_node, exposeSchedulerInRepository_node)
        xml_util.add_child_node(SchedulerFactoryBean_node, autoStartup_node)
        xml_util.add_child_node(SchedulerFactoryBean_node, startupDelay_node)
        xml_util.add_child_node(SchedulerFactoryBean_node, applicationContextSchedulerContextKey_node)
        xml_util.add_child_node(SchedulerFactoryBean_node, configLocation_node)
        xml_util.add_child_node(SchedulerFactoryBean_node, jobFactory_node)
        xml_util.add_child_node(SchedulerFactoryBean_node, triggers_node)
        xml_util.add_child_node(root, SchedulerFactoryBean_node)
            
        xml_util.write_xml(tree, converted_file_path)
        
    print '转换完毕!!!'
def load_xml_files():
    """
    读取需要转换的xml文件列表
    """
    source_xml_files = glob.glob(source_file_parent_path + "/*.xml")
    return source_xml_files

convert()

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
                     
            targetObject = targetObject_node.attrib['ref']   
            targetMethod = targetMethod_node.attrib['value']
            
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
        jobFactory_node = xml_util.create_node("property",{"name":"jobFactory","value":job_factory_class},'')
        
        xml_util.add_child_nodes(SchedulerFactoryBean_nodes, dataSource_node)
        xml_util.add_child_nodes(SchedulerFactoryBean_nodes, overwriteExistingJobs_node)
        xml_util.add_child_nodes(SchedulerFactoryBean_nodes, exposeSchedulerInRepository_node)
        xml_util.add_child_nodes(SchedulerFactoryBean_nodes, autoStartup_node)
        xml_util.add_child_nodes(SchedulerFactoryBean_nodes, startupDelay_node)
        xml_util.add_child_nodes(SchedulerFactoryBean_nodes, applicationContextSchedulerContextKey_node)
        xml_util.add_child_nodes(SchedulerFactoryBean_nodes, configLocation_node)
        xml_util.add_child_nodes(SchedulerFactoryBean_nodes, jobFactory_node)
        
        xml_util.write_xml(tree, converted_file_path)
    print '转换完毕!!!'
def load_xml_files():
    """
    读取需要转换的xml文件列表
    """
    source_xml_files = glob.glob(source_file_parent_path + "/*.xml")
    return source_xml_files

convert()

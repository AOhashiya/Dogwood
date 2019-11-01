# -*- coding: utf-8 -*-
# sqls.py
# INSERT ---------------------------------------------------------------------
insert_m_company = """
   INSERT INTO m_company (
      company_name,
      responsible,
      industry,
      adopt_date,
      is_foreigner,
      mail,
      phone_number,
      entry_date,
      update_date
   )
   VALUES (
      [company],
      [name],
      [industry],
      [date],
      [foreigner],
      [mail],
      [tel],
      NOW(),
      NOW()
   )
"""
insert_s_user_sns = """
   INSERT INTO s_user_sns (
      user_id,
      fb_id,
      fb_name,
      fb_image,
      fb_mail
   )
   VALUES (
      [user_id],
      [fb_id],
      [fb_name],
      [fb_image],
      [fb_mail]
   )
"""
insert_s_user_policy = """
   INSERT INTO s_user_policy (
      user_id,
      policy_version
   )
   VALUES (
      [user_id],
      [policy_version]
   )
"""
insert_m_user = """
   INSERT INTO m_user (
      user_id,
      user_key,
      name,
      name_ruby,
      gender,
      birthdate,
      nationality,
      japanese_level,
      language,
      mail,
      phone_number,
      address_0,
      address_1,
      address_2,
      visa_status,
      visa_expiration,
      preferred_jobtype,
      jobchange_date,
      salary,
      work_location,
      college,
      final_education,
      license,
      career,
      jobchange,
      specified_skilled,
      specified_skilled_plans,
      entry_date
   )
   VALUES (
      [user_id],
      [user_key],
      [name],
      [ename],
      [gender],
      [birthdate],
      [nationality],
      [japanese],
      [language],
      [mail],
      [phone],
      [address_0],
      [pref31],
      [addr31],
      [visa],
      [visa_expiration],
      [jobtype],
      [jobchange_date],
      [salary],
      [work_location],
      [college],
      [final_education],
      [license],
      [career],
      [jobchange],
      [specific_skills],
      [specified_skilled_plans],
      NOW()
   )
"""
# UPDATE ---------------------------------------------------------------------
update_s_user_policy = """
   UPDATE s_user_policy SET policy_version = [policy_version]
   WHERE user_id = [user_id]
"""
update_m_user = """
   UPDATE m_user SET
      name              = [name],
      name_ruby         = [ename],
      gender            = [gender],
      birthdate         = [birthdate],
      nationality       = [nationality],
      japanese_level    = [japanese],
      language          = [language],
      mail              = [mail],
      phone_number      = [phone],
      address_0         = [address_0],
      address_1         = [pref31],
      address_2         = [addr31],
      visa_status       = [visa],
      visa_expiration   = [visa_expiration],
      preferred_jobtype = [jobtype],
      jobchange_date    = [jobchange_date],
      salary            = [salary],
      work_location     = [work_location],
      college           = [college],
      final_education   = [final_education],
      license           = [license],
      career            = [career],
      jobchange         = [jobchange],
      specified_skilled = [specific_skills],
      specified_skilled_plans = [specified_skilled_plans]
   WHERE user_id = [user_id]
"""
# SELECT ---------------------------------------------------------------------
selectAll_s_user_sns = """
   SELECT * FROM s_user_sns
"""
selectUserID_s_fb_user_sns = """
   SELECT user_id FROM s_user_sns
   WHERE fb_id = [fb_id]
"""
selectHas_s_user_sns = """
   SELECT COUNT(user_id) AS cnt FROM s_user_sns
   WHERE user_id = [user_id]
"""
selectHas_m_user = """
    SELECT COUNT(user_id) AS cnt FROM m_user
    WHERE user_id = [user_id]
"""
selectHas_m_user_key = """
    SELECT COUNT(user_id) AS cnt FROM m_user
    WHERE user_key = [user_key]
"""
select_m_privacy_policy = """
    SELECT text FROM m_privacy_policy
    ORDER BY version DESC LIMIT 1
"""
selectForm_m_user = """
    SELECT
      user_id,
      name,
      name_ruby AS ename,
      gender,
      DATE_FORMAT(birthdate, '%Y-%m-%d') AS birthdate,
      DATE_FORMAT(birthdate, '%Y') AS year,
      DATE_FORMAT(birthdate, '%m') AS month,
      DATE_FORMAT(birthdate, '%d') AS day,
      nationality,
      japanese_level AS japanese,
      language,
      mail,
      phone_number AS phone,
      address_0,
      address_1 AS pref31,
      address_2 AS addr31,
      visa_status AS visa,
      DATE_FORMAT(visa_expiration, '%Y-%m-%d') AS visa_expiration,
      DATE_FORMAT(visa_expiration, '%Y') AS expiration_year,
      DATE_FORMAT(visa_expiration, '%m') AS expiration_month,
      DATE_FORMAT(visa_expiration, '%d') AS expiration_day,
      preferred_jobtype AS jobtype,
      DATE_FORMAT(jobchange_date, '%Y-%m-%d') AS jobchange_date,
      DATE_FORMAT(jobchange_date, '%Y') AS jobchange_date_year,
      DATE_FORMAT(jobchange_date, '%m') AS jobchange_date_month,
      DATE_FORMAT(jobchange_date, '%d') AS jobchange_date_day,
      salary,
      work_location,
      college,
      final_education,
      license,
      career,
      jobchange,
      specified_skilled AS specific_skills,
      specified_skilled_plans,
      entry_date
    FROM m_user
    WHERE user_id = [user_id]
"""
select_s_user_policy = """
    SELECT * FROM s_user_policy
    WHERE user_id = [user_id]
"""
# End

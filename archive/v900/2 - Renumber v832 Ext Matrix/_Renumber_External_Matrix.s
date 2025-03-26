
;renumber external matrices fromm old to new numbering scheme
RUN PGM=MATRIX  MSG='Renuber External Matrices from v832 to v9'
FILEI MATI[1] = 'WF_External - 2019\WF_ExtTripTable_DY.mtx'

FILEO MATO[1] = 'WF_ExtTripTable_DY.mtx',
    mo=101-151,
    name=Total         ,
         Pass_LT       ,
         MD_Truck      ,
         HV_Truck      ,
         II_LH_MD      ,
         II_LH_HV      ,
         IX_HBW        ,
         IX_HBO        ,
         IX_NHB        ,
         IX_HBS        ,
         IX_HBC        ,
         IX_REC        ,
         IX_Ext_Bus    ,
         IX_Ext_Oth    ,
         IX_Ext_Rec    ,
         IX_Ext_MD     ,
         IX_SH_LT      ,
         IX_SH_MD      ,
         IX_SH_HV      ,
         IX_LH_MD      ,
         IX_LH_HV      ,
         XI_HBW        ,
         XI_HBO        ,
         XI_NHB        ,
         XI_HBS        ,
         XI_HBC        ,
         XI_REC        ,
         XI_Ext_Bus    ,
         XI_Ext_Oth    ,
         XI_Ext_Rec    ,
         XI_Ext_MD     ,
         XI_SH_LT      ,
         XI_SH_MD      ,
         XI_SH_HV      ,
         XI_LH_MD      ,
         XI_LH_HV      ,
         XX_HBW        ,
         XX_HBO        ,
         XX_NHB        ,
         XX_HBS        ,
         XX_HBC        ,
         XX_REC        ,
         XX_Ext_Bus    ,
         XX_Ext_Oth    ,
         XX_Ext_Rec    ,
         XX_Ext_MD     ,
         XX_SH_LT      ,
         XX_SH_MD      ,
         XX_SH_HV      ,
         XX_LH_MD      ,
         XX_LH_HV      
    
    
    
    ;set MATRIX parameters
    ZONES = 3629
    
    
    
    ;assign work matricesTotal
    mw[101] = mi.1.Total               ;Total
    mw[102] = mi.1.Pass_LT             ;Pass_LT
    mw[103] = mi.1.MD_Truck            ;MD_Truck
    mw[104] = mi.1.HV_Truck            ;HV_Truck
    mw[105] = mi.1.II_LH_MD            ;II_LH_MD
    mw[106] = mi.1.II_LH_HV            ;II_LH_HV
    mw[107] = mi.1.IX_HBW              ;IX_HBW
    mw[108] = mi.1.IX_HBO              ;IX_HBO
    mw[109] = mi.1.IX_NHB              ;IX_NHB
    mw[110] = mi.1.IX_HBS              ;IX_HBS
    mw[111] = mi.1.IX_HBC              ;IX_HBC
    mw[112] = mi.1.IX_REC              ;IX_REC
    mw[113] = mi.1.IX_Ext_Bus          ;IX_Ext_Bus
    mw[114] = mi.1.IX_Ext_Oth          ;IX_Ext_Oth
    mw[115] = mi.1.IX_Ext_Rec          ;IX_Ext_Rec
    mw[116] = mi.1.IX_Ext_MD           ;IX_Ext_MD
    mw[117] = mi.1.IX_SH_LT            ;IX_SH_LT
    mw[118] = mi.1.IX_SH_MD            ;IX_SH_MD
    mw[119] = mi.1.IX_SH_HV            ;IX_SH_HV
    mw[120] = mi.1.IX_LH_MD            ;IX_LH_MD
    mw[121] = mi.1.IX_LH_HV            ;IX_LH_HV
    mw[122] = mi.1.XI_HBW              ;XI_HBW
    mw[123] = mi.1.XI_HBO              ;XI_HBO
    mw[124] = mi.1.XI_NHB              ;XI_NHB
    mw[125] = mi.1.XI_HBS              ;XI_HBS
    mw[126] = mi.1.XI_HBC              ;XI_HBC
    mw[127] = mi.1.XI_REC              ;XI_REC
    mw[128] = mi.1.XI_Ext_Bus          ;XI_Ext_Bus
    mw[129] = mi.1.XI_Ext_Oth          ;XI_Ext_Oth
    mw[130] = mi.1.XI_Ext_Rec          ;XI_Ext_Rec
    mw[131] = mi.1.XI_Ext_MD           ;XI_Ext_MD
    mw[132] = mi.1.XI_SH_LT            ;XI_SH_LT
    mw[133] = mi.1.XI_SH_MD            ;XI_SH_MD
    mw[134] = mi.1.XI_SH_HV            ;XI_SH_HV
    mw[135] = mi.1.XI_LH_MD            ;XI_LH_MD
    mw[136] = mi.1.XI_LH_HV            ;XI_LH_HV
    mw[137] = mi.1.XX_HBW              ;XX_HBW
    mw[138] = mi.1.XX_HBO              ;XX_HBO
    mw[139] = mi.1.XX_NHB              ;XX_NHB
    mw[140] = mi.1.XX_HBS              ;XX_HBS
    mw[141] = mi.1.XX_HBC              ;XX_HBC
    mw[142] = mi.1.XX_REC              ;XX_REC
    mw[143] = mi.1.XX_Ext_Bus          ;XX_Ext_Bus
    mw[144] = mi.1.XX_Ext_Oth          ;XX_Ext_Oth
    mw[145] = mi.1.XX_Ext_Rec          ;XX_Ext_Rec
    mw[146] = mi.1.XX_Ext_MD           ;XX_Ext_MD
    mw[147] = mi.1.XX_SH_LT            ;XX_SH_LT
    mw[148] = mi.1.XX_SH_MD            ;XX_SH_MD
    mw[149] = mi.1.XX_SH_HV            ;XX_SH_HV
    mw[150] = mi.1.XX_LH_MD            ;XX_LH_MD
    mw[151] = mi.1.XX_LH_HV            ;XX_LH_HV

    
    
    ;renumber working matrices
    RENUMBER FILE='renumber.txt', missingzi=m, missingzo=m
    
ENDRUN